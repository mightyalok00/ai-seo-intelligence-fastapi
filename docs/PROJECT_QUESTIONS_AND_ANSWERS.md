# AI SEO Intelligence FastAPI — Project Questions and Answers

## Project objective

Build a structured FastAPI application that combines a strict, explainable SEO audit, machine-learning search-intent classification, recommendations, and a browser dashboard.

The score measures supplied audit signals. It does **not** predict or guarantee Google rankings.

### 1. Can the API audit a page and return an overall score?

Yes. `POST /api/analyze` evaluates 16 categories with fixed weights totaling 100. It returns `overall_score`, `grade`, and the full category breakdown.

### 2. Why is 100/100 difficult?

Presence alone earns little or no credit. Full marks require ideal title and meta quality, strong heading structure, substantial content, researched semantic coverage, healthy links and ALT text, valid rich schema, a self-referencing canonical, explicit indexability, natural keyword distribution, good readability, intent alignment, a clean URL, and complete technical evidence.

### 3. Is this a Google ranking score?

No. It is a deterministic audit completeness score. Google rankings depend on many page-level, site-level, competitive, behavioral, and algorithmic factors beyond this application.

### 4. How are the grades assigned?

Exceptional is 90–100, Strong is 80–89, Good but needs improvement is 70–79, Average is 60–69, Weak is 40–59, and Poor is 0–39.

### 5. What does each category return?

Every entry in `category_scores` contains `score`, `max`, `issues`, and `recommendations`. This makes deductions visible and reproducible.

### 6. How are the most important findings organized?

The response separates `critical_issues`, `warnings`, `passed_checks`, and `priority_recommendations`. Critical items include blocking indexability, missing essential elements, severe thin content, HTTP errors, and likely keyword stuffing.

### 7. Which inputs does the audit accept?

It accepts keyword, URL, title, meta description, H1, H2s, content, semantic terms, internal links, external links, image ALT values, schema JSON-LD, canonical URL, robots/indexability signals, and an optional nested technical object.

### 8. Which technical inputs are supported?

The optional technical object accepts HTTPS, mobile friendliness, PageSpeed score, HTTP status, viewport, favicon, sitemap, and broken-link count. Unknown values do not receive points.

### 9. Can the model still classify search intent?

Yes. The TF-IDF and Logistic Regression pipeline remains unchanged. It predicts informational, commercial, transactional, or navigational intent and returns confidence.

### 10. How does the audit use predicted intent?

The intent-match category checks whether the title, meta description, headings, body cues, and expected page action or format align with the ML-predicted intent.

### 11. Are keyword calculations deterministic?

Yes. Exact phrases are counted with word boundaries. Density accounts for the number of words in the target phrase and is used alongside early placement, page distribution, and repetition checks.

### 12. Can it compare content and suggest metadata?

Yes. `POST /api/content-gap` returns meaningful competitor terms missing from primary content. Deterministic title and meta-description suggestions remain in the main audit response.

### 13. Does the project require SQL or a database?

No. The API is stateless and has no SQL dependency, database file, persistence service, or history endpoint. Each audit is calculated and returned directly.

### 14. How is the browser interface different?

The interface now captures all audit signals and renders the overall score, grade, progress indicator, 16 category cards, critical issues, warnings, passed checks, and prioritized recommendations. It remains responsive and links directly to Swagger.

### 15. How is the project verified?

Pytest covers the exact 100-point weighting, grade boundaries, deterministic scoring, penalties for missing data, response structure, stateless API behavior, frontend/static delivery, Swagger, intent prediction, and content-gap analysis. Pydantic returns HTTP 422 for invalid request data, and a missing ML model returns HTTP 503 with recovery instructions.
