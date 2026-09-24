from app.services.seo_analyzer import (
    CATEGORY_WEIGHTS,
    analyze_seo,
    content_gap,
    grade_for_score,
    keyword_metrics,
)


def base_audit(**overrides):
    data = {
        "keyword": "seo tools",
        "url": "https://example.com/seo-tools",
        "title": "SEO Tools: Compare Features, Benefits and Pricing Today",
        "meta_description": (
            "Compare SEO tools for keyword research, technical audits, content "
            "optimization, and reporting. Discover the right platform for your team."
        ),
        "h1": "Compare SEO Tools for a Better Marketing Workflow",
        "h2s": ["SEO Tools Compared", "Keyword Research Guide", "Compare Pricing and Features"],
        "content": (
            "SEO tools support keyword research, technical audit workflows, content "
            "optimization, backlink analysis, rank tracking, reporting dashboard work, "
            "competitor analysis, and search visibility. Compare features and pricing "
            "in this practical guide with useful examples and tips. "
        ) * 12,
        "semantic_terms": [
            "keyword research",
            "technical audit",
            "content optimization",
            "backlink analysis",
            "rank tracking",
            "reporting dashboard",
            "competitor analysis",
            "search visibility",
        ],
        "internal_links": ["/one", "/two", "/three", "/four", "/five"],
        "external_links": ["https://developers.google.com/search/docs", "https://schema.org"],
        "image_alts": [
            "SEO tools comparison dashboard screenshot",
            "Keyword research report for marketing teams",
            "Technical audit chart with website issues",
        ],
        "schema_json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "SEO Tools Compared",
            "description": "Comparison",
            "author": {"@type": "Person", "name": "Team"},
        },
        "canonical": "https://example.com/seo-tools",
        "robots_indexable": True,
        "robots_directives": "index, follow",
        "technical": {
            "https": True,
            "mobile_friendly": True,
            "page_speed_score": 95,
            "status_code": 200,
            "has_viewport": True,
            "has_favicon": True,
            "has_sitemap": True,
            "broken_links": 0,
        },
        "predicted_intent": "commercial",
    }
    data.update(overrides)
    return analyze_seo(**data)


def test_keyword_metrics_uses_exact_phrase():
    metrics = keyword_metrics("seo", "SEO is useful. SEOs differ. SEO helps websites.")
    assert metrics["frequency"] == 2
    assert metrics["density"] > 0


def test_weights_total_exactly_100_and_result_is_deterministic():
    first = base_audit()
    second = base_audit()
    assert sum(CATEGORY_WEIGHTS.values()) == 100
    assert first == second
    assert first["overall_score"] == sum(
        item["score"] for item in first["category_scores"].values()
    )


def test_full_score_is_difficult_and_missing_data_is_penalized():
    strong = base_audit()
    incomplete = base_audit(
        semantic_terms=[],
        internal_links=[],
        external_links=[],
        image_alts=[],
        schema_json_ld=None,
        canonical="",
        robots_indexable=None,
        robots_directives="",
        technical={},
    )
    assert strong["overall_score"] > incomplete["overall_score"]
    assert incomplete["overall_score"] < 70
    assert incomplete["category_scores"]["schema"]["score"] == 0
    assert incomplete["category_scores"]["image_alt"]["score"] == 0


def test_grade_boundaries():
    assert grade_for_score(90) == "Exceptional"
    assert grade_for_score(80) == "Strong"
    assert grade_for_score(70) == "Good but needs improvement"
    assert grade_for_score(60) == "Average"
    assert grade_for_score(40) == "Weak"
    assert grade_for_score(39) == "Poor"


def test_content_gap():
    missing = content_gap(
        "keyword research content",
        "keyword research backlinks technical audit reporting",
    )
    assert "backlinks" in missing

