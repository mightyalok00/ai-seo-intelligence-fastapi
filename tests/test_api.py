import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.seo_analyzer import CATEGORY_WEIGHTS


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def complete_payload():
    content = (
        "Best SEO tools help teams compare keyword research, technical audit, "
        "content optimization, backlink analysis, rank tracking, competitor analysis, "
        "search visibility, and reporting dashboard features. This practical guide "
        "explains platform benefits, pricing, workflow, examples, and selection tips. "
    ) * 12
    return {
        "keyword": "best seo tools",
        "url": "https://example.com/best-seo-tools",
        "title": "Best SEO Tools: Compare Features, Benefits and Pricing",
        "meta_description": (
            "Compare the best SEO tools for research, technical audits, content "
            "optimization, and reporting. Discover the right platform for your team."
        ),
        "h1": "Compare the Best SEO Tools for Modern Marketing Teams",
        "h2s": [
            "Best SEO Tools Compared",
            "Keyword Research and Content Features",
            "Technical Audit and Backlink Analysis",
            "Compare Pricing and Reporting",
        ],
        "content": content,
        "semantic_terms": [
            "keyword research",
            "technical audit",
            "content optimization",
            "backlink analysis",
            "rank tracking",
            "competitor analysis",
            "search visibility",
            "reporting dashboard",
        ],
        "internal_links": [
            "/seo-guide",
            "/keyword-research",
            "/technical-seo",
            "/content-optimization",
            "/contact",
        ],
        "external_links": [
            "https://developers.google.com/search/docs",
            "https://schema.org/Article",
        ],
        "image_alts": [
            "SEO tools comparison dashboard screenshot",
            "Keyword research chart for SEO software",
            "Technical audit report showing website issues",
        ],
        "schema_json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Best SEO Tools Compared",
            "description": "A detailed comparison of SEO tools",
            "author": {"@type": "Person", "name": "SEO Team"},
        },
        "canonical": "https://example.com/best-seo-tools",
        "robots_indexable": True,
        "robots_directives": "index, follow",
        "technical": {
            "https": True,
            "mobile_friendly": True,
            "page_speed_score": 92,
            "status_code": 200,
            "has_viewport": True,
            "has_favicon": True,
            "has_sitemap": True,
            "broken_links": 0,
        },
    }


def test_health_frontend_and_docs(client):
    assert client.get("/api/health").json()["status"] == "ok"
    home = client.get("/")
    assert home.status_code == 200
    assert "Strict 16-category audit" in home.text
    assert 'id="theme-toggle"' in home.text
    assert 'id="export-json"' in home.text
    assert 'id="print-report"' in home.text
    assert 'id="score-chart"' in home.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/docs").status_code == 200


def test_validation_error_for_short_content(client):
    payload = complete_payload()
    payload["content"] = "too short"
    assert client.post("/api/analyze", json=payload).status_code == 422


def test_analyze_returns_weighted_audit(client):
    response = client.post("/api/analyze", json=complete_payload())
    assert response.status_code == 200
    analysis = response.json()

    assert "analysis_id" not in analysis
    assert 0 <= analysis["overall_score"] <= 100
    assert analysis["grade"] in {
        "Exceptional",
        "Strong",
        "Good but needs improvement",
        "Average",
        "Weak",
        "Poor",
    }
    assert set(analysis["category_scores"]) == set(CATEGORY_WEIGHTS)
    assert sum(item["max"] for item in analysis["category_scores"].values()) == 100
    for name, maximum in CATEGORY_WEIGHTS.items():
        item = analysis["category_scores"][name]
        assert item["max"] == maximum
        assert 0 <= item["score"] <= maximum
        assert isinstance(item["issues"], list)
        assert isinstance(item["recommendations"], list)

    for key in (
        "critical_issues",
        "warnings",
        "passed_checks",
        "priority_recommendations",
    ):
        assert isinstance(analysis[key], list)

    assert client.get("/api/history").status_code == 404


def test_missing_essentials_create_critical_issues(client):
    payload = complete_payload()
    payload.update({
        "title": "",
        "meta_description": "",
        "h1": "",
        "canonical": "",
        "robots_indexable": False,
        "robots_directives": "noindex, nofollow",
    })
    analysis = client.post("/api/analyze", json=payload).json()
    assert analysis["overall_score"] < 80
    assert "Missing page title" in analysis["critical_issues"]
    assert "Page is not indexable" in analysis["critical_issues"]


def test_predict_intent_and_content_gap(client):
    prediction = client.post(
        "/api/predict-intent",
        json={"keyword": "google search console login"},
    )
    gap = client.post(
        "/api/content-gap",
        json={
            "primary_content": "Keyword research and useful content planning basics.",
            "competitor_content": (
                "Keyword research, technical audits, backlink analysis, reporting, "
                "and detailed competitor monitoring workflows."
            ),
        },
    )
    assert prediction.status_code == 200
    assert 0 <= prediction.json()["confidence"] <= 1
    assert gap.status_code == 200
    assert "technical" in gap.json()["missing_topics"]
