# AI SEO Intelligence FastAPI

A portfolio-ready FastAPI application that produces a strict, transparent SEO audit, predicts search intent with machine learning, and presents results in a responsive browser dashboard.

> The 0–100 result is an **audit completeness score**, not a Google ranking score, ranking prediction, or guarantee.

## What changed in version 2

The former deduction-based score was replaced with 16 independently scored categories. Each category uses several deterministic checks, so merely supplying a field does not earn full points. A 100/100 requires ideal content, semantic, linking, structured-data, indexability, URL, and technical signals at the same time.

| Category | Points |
|---|---:|
| Title | 8 |
| Meta Description | 7 |
| H1/H2 Structure | 7 |
| Content Depth | 10 |
| Semantic Terms | 8 |
| Internal Links | 6 |
| External Links | 4 |
| Image ALT | 5 |
| Schema | 6 |
| Canonical | 4 |
| Robots / Indexability | 6 |
| Keyword Usage / Stuffing | 7 |
| Readability | 6 |
| Search Intent Match | 7 |
| URL Quality | 4 |
| Technical Checks | 5 |
| **Total** | **100** |

Grades:

- 90–100: Exceptional
- 80–89: Strong
- 70–79: Good but needs improvement
- 60–69: Average
- 40–59: Weak
- 0–39: Poor

## Main features

- Granular, deterministic scoring with exact category weights
- Issues and recommendations for every category
- Critical issues, warnings, passed checks, and prioritized actions
- Exact-phrase keyword frequency and density
- Search-intent classification: informational, commercial, transactional, or navigational
- Content-gap comparison
- Title and meta-description suggestions
- Redesigned HTML/CSS/JavaScript audit dashboard
- Swagger and ReDoc API documentation
- Automated service and API tests
- Docker support

## Project structure

```text
ai-seo-intelligence-fastapi/
├── app/
│   ├── api/routes.py
│   ├── schemas/seo_schema.py
│   ├── services/intent_model.py
│   ├── services/seo_analyzer.py
│   └── main.py
├── data/search_intent_keywords.csv
├── docs/PROJECT_QUESTIONS_AND_ANSWERS.md
├── frontend/
│   ├── static/app.js
│   ├── static/styles.css
│   └── templates/index.html
├── model/intent_model.pkl
├── notebooks/seo_fastapi_walkthrough.ipynb
├── tests/
├── train_model.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## Run in VS Code

Use Python 3.12 to match the pinned packages and Docker image.

### 1. Create and activate the environment

PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate
```

### 2. Install, train, and start

```bash
pip install -r requirements.txt
python train_model.py
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 3. Run tests

```bash
python -m pytest -q
```

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Strict 100-point SEO audit |
| POST | `/api/predict-intent` | ML search-intent prediction |
| POST | `/api/content-gap` | Missing-topic comparison |

## Audit request

```json
{
  "keyword": "best seo tools",
  "url": "https://example.com/best-seo-tools",
  "title": "Best SEO Tools: Compare Features and Pricing",
  "meta_description": "Compare the best SEO tools for research, audits, content optimization, and reporting. Discover the right platform for your team.",
  "h1": "Compare the Best SEO Tools for Modern Marketing",
  "h2s": ["Best SEO Tools Compared", "Keyword Research", "Technical Audits"],
  "content": "Long-form page content...",
  "semantic_terms": ["keyword research", "technical audit", "rank tracking"],
  "internal_links": ["/seo-guide", "/keyword-research"],
  "external_links": ["https://developers.google.com/search/docs"],
  "image_alts": ["SEO tools comparison dashboard screenshot", ""],
  "schema_json_ld": {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Best SEO Tools Compared"
  },
  "canonical": "https://example.com/best-seo-tools",
  "robots_indexable": true,
  "robots_directives": "index, follow",
  "technical": {
    "https": true,
    "mobile_friendly": true,
    "page_speed_score": 92,
    "status_code": 200,
    "has_viewport": true,
    "has_favicon": true,
    "has_sitemap": true,
    "broken_links": 0
  }
}
```

Optional technical values can be omitted or sent as `null`. Unknown evidence does not receive credit, which keeps the audit honest.

## Response contract

`POST /api/analyze` returns:

- `overall_score` and `grade`
- `category_scores`, each with `score`, `max`, `issues`, and `recommendations`
- `critical_issues`, `warnings`, `passed_checks`, and `priority_recommendations`
- ML `search_intent` and `intent_confidence`
- `keyword_frequency` and `keyword_density`
- deterministic title/meta suggestions

The API is intentionally stateless and uses no SQL database. The scoring rules are explainable and reproducible. They are useful for page QA and prioritization, but real search performance also depends on competition, authority, crawl behavior, links, user satisfaction, algorithms, and many other factors outside this audit.
