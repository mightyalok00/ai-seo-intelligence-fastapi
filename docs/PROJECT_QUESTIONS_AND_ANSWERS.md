# AI SEO Intelligence FastAPI: Project Questions and Answers

This document answers the 15 project questions from the repository's assignment/viva set. The answers describe the current implementation, including what the application does and does not automate.

> The application's 0-100 result is a deterministic audit-completeness score. It is not a Google ranking score, ranking prediction, or guarantee.

## 1. What is the main objective of the AI SEO Intelligence FastAPI project, and what SEO problems does it solve?

The project turns structured page evidence into an explainable on-page SEO audit. A user supplies a target keyword and signals such as the title, meta description, headings, content, links, image ALT text, schema, canonical URL, robots settings, and technical measurements. The application then:

- calculates a weighted score across 16 categories;
- predicts one of four search-intent classes with a trained machine-learning model;
- reports exact issues, recommendations, passed checks, and priorities;
- calculates exact-phrase keyword frequency and density;
- suggests a title and meta description;
- compares primary and competitor text for content gaps; and
- displays audit results in a browser dashboard.

The application helps make common SEO quality checks consistent and transparent. It does not crawl a URL, retrieve live metrics, store audit history, or predict search rankings; it evaluates the evidence supplied in the request.

## 2. How does FastAPI handle SEO audit requests and return analysis results through API endpoints?

`app/main.py` creates the FastAPI application, mounts the static frontend at `/static`, serves the dashboard at `/`, and includes the API router under `/api`. The main endpoints are:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Return service health information. |
| `POST` | `/api/analyze` | Run intent prediction and the complete 16-category audit. |
| `POST` | `/api/predict-intent` | Classify a keyword and return its confidence. |
| `POST` | `/api/content-gap` | Find meaningful competitor terms missing from primary content. |

Pydantic models in `app/schemas/seo_schema.py` validate request fields and constrain lengths and numeric ranges. For `/api/analyze`, the route first predicts search intent, passes the validated page evidence to `analyze_seo()`, adds deterministic title/meta suggestions, and validates the result against `SEOAnalysisResponse`. Invalid input produces FastAPI's HTTP 422 response. If the serialized intent model is missing, the intent-dependent endpoints return HTTP 503 with instructions to run `python train_model.py`.

The API is stateless: it returns each result directly and has no database or history endpoint.

## 3. How is the overall SEO audit score calculated out of 100 using the 16 SEO categories?

`CATEGORY_WEIGHTS` in `app/services/seo_analyzer.py` defines fixed maximums that total exactly 100:

| Category | Maximum points |
|---|---:|
| Title | 8 |
| Meta description | 7 |
| H1/H2 structure | 7 |
| Content depth | 10 |
| Semantic terms | 8 |
| Internal links | 6 |
| External links | 4 |
| Image ALT | 5 |
| Schema | 6 |
| Canonical | 4 |
| Robots/indexability | 6 |
| Keyword usage/stuffing | 7 |
| Readability | 6 |
| Search intent match | 7 |
| URL quality | 4 |
| Technical checks | 5 |
| **Total** | **100** |

Each category applies several deterministic rules and returns `score`, `max`, `issues`, and `recommendations`. The helper `_category()` clamps a category result between zero and its maximum and rounds it to one decimal place. The overall score is the rounded sum of all category scores, clamped to 0-100.

The grade is derived from the final score: Exceptional (90-100), Strong (80-89), Good but needs improvement (70-79), Average (60-69), Weak (40-59), or Poor (0-39).

## 4. How does the system evaluate the SEO quality of the page title and meta description?

The **title category (8 points)** checks:

- whether a title exists (1 point);
- whether it contains the exact target phrase (2 points) and starts with it (1 additional point);
- whether its length is ideal at 50-60 characters (2 points), or acceptable at 40-69 (1 point);
- whether wording avoids excessive repetition and exclamation marks (1 point); and
- whether it contains a cue associated with the predicted intent (1 point).

A missing title becomes a critical issue.

The **meta-description category (7 points)** checks:

- whether a description exists (1 point);
- ideal length of 140-160 characters (2 points), or acceptable length of 120-170 (1 point);
- exact target-keyword inclusion (1 point);
- a predicted-intent cue (1 point);
- an action or benefit word such as `discover`, `learn`, `compare`, `get`, `find`, `explore`, or `choose` (1 point); and
- non-duplicative wording with keyword density no higher than 4% (1 point).

A missing meta description is also a critical issue. These checks are deterministic string rules, not SERP preview measurements.

## 5. How does the project analyze H1 and H2 heading structure and identify heading-related SEO issues?

The H1/H2 category is worth 7 points. The analyzer gives one point for a present H1, two points when the H1 contains the exact target keyword, and one point when the H1 is not identical to the title. A missing H1 is a critical issue; a missing keyword or duplicate title/H1 produces an issue and recommendation.

For H2s, three or more non-empty headings earn two points, while one or two earn one point. No H2s, or too few H2s, produces guidance to add useful sections. The final point is awarded when supplied semantic terms appear in the combined H1/H2 text: at least two matches are required when two or more terms were supplied, otherwise every supplied term must match.

The request schema accepts one `h1` string and a list of up to 50 `h2s`. It does not parse a live HTML document or count multiple H1 elements; it evaluates the supplied heading data.

## 6. How does the system measure content depth, keyword frequency, keyword density, and possible keyword stuffing?

Content depth is worth 10 points. Word-count tiers award up to five points: 200, 400, 700, 1,000, and 1,500 words. Additional points come from placing the keyword in the first 100 words, having at least 12 sentences, providing enough paragraph/section structure, and covering supplied semantic terms. Content below 1,000 words receives an expansion recommendation, and content below 200 words is marked critically thin.

`keyword_metrics()` normalizes whitespace and case, then counts the target keyword as an exact phrase with word boundaries. Keyword density is:

```text
(exact-phrase occurrences x words in the target phrase / total content words) x 100
```

The keyword-usage category is worth 7 points. Its conservative ideal density is 0.5%-1.5%; broader partial-credit bands extend to 3%. Density above 3% creates a critical "Possible keyword stuffing" finding. The category also checks for at least two occurrences, early placement, distribution across all three thirds of the content, and the absence of three or more adjacent repeated exact-match phrases.

## 7. How are semantic terms identified and used to evaluate the topical relevance of webpage content?

Semantic terms are **not discovered automatically** by the audit. The user supplies a researched list of related entities, subtopics, or natural variants in `semantic_terms`. The analyzer normalizes and de-duplicates that list, then performs exact-phrase, case-insensitive matches against the body and headings.

The 8-point semantic category scores body coverage ratio (up to 5 points), breadth of the supplied set (up to 2 points, with the maximum at eight or more unique terms), and whether a covered term also appears in a heading (1 point). It reports up to five missing terms and recommends adding only relevant concepts.

Semantic coverage also contributes to content-depth and heading-structure scores. Separately, `/api/content-gap` tokenizes primary and competitor text, removes a built-in stopword list and very short tokens, and returns up to 15 frequent competitor terms absent from the primary content. That endpoint is a simple lexical comparison, not an embedding or large-language-model analysis.

## 8. How does the SEO analyzer evaluate internal links and external links, and why are both important for SEO?

The internal-link category is worth 6 points. It awards up to four points based on the number of supplied links, with the maximum at five or more. One point is awarded when all supplied values are accepted as valid, and one point when there are at least four distinct destination paths. Relative paths beginning with `/` and syntactically valid absolute HTTP(S) URLs are accepted.

The external-link category is worth 4 points. It awards up to two points for quantity, with the maximum at two or more valid HTTP(S) URLs, one point when every valid external link uses HTTPS, and one point for at least two distinct domains.

Internal links help users and crawlers discover related site content and distribute navigation context. External links can support claims with authoritative sources. The current implementation validates strings and diversity only: it does not crawl destinations, verify that an absolute "internal" URL shares the audited host, test response status, or judge source authority.

## 9. How does the system check image ALT attributes, canonical tags, robots/indexability settings, and schema markup?

- **Image ALT (5 points):** scores non-empty coverage, whether every non-empty description is 5-15 words, and topical relevance when at least three ALT samples exist. Blank list entries represent missing ALT text. It does not inspect image files.
- **Canonical (4 points):** checks presence, absolute HTTP(S) validity, same host as the audited URL, and exact self-reference after ignoring a trailing slash. A missing canonical is critical.
- **Robots/indexability (6 points):** uses the explicit `robots_indexable` value plus comma-separated directives. Confirmed indexability earns three points; supplied directives, absence of `noindex`/`nofollow`, and explicit `index, follow` earn the remaining points. Non-indexability or `noindex` can become critical.
- **Schema (6 points):** accepts a JSON object, array, or JSON string; checks valid shape, `@context`, `@type`, a recognized common type, at least five properties on a node, and a useful entity property such as `headline`, `name`, `mainEntity`, or `offers` (or multiple nodes).

These are deterministic validation heuristics. The application does not fetch rendered markup or submit schema to an external rich-results validator.

## 10. How does the machine-learning model classify search intent into informational, commercial, transactional, and navigational categories?

The trained artifact is a scikit-learn `Pipeline` with two stages:

1. `TfidfVectorizer(ngram_range=(1, 2), lowercase=True)` converts lowercased keyword unigrams and bigrams into TF-IDF features.
2. `LogisticRegression(max_iter=1000, random_state=42, solver="liblinear")` predicts one of the four labels.

`IntentPredictor` in `app/services/intent_model.py` lazily loads `model/intent_model.pkl` with Joblib the first time a prediction is requested, then reuses it for later requests in the process. `predict()` sends the keyword through the pipeline, uses the largest `predict_proba()` value as confidence, rounds confidence to four decimals, and returns the predicted label.

## 11. What dataset and preprocessing steps are used to train the search-intent classification model, and how is the trained model saved and loaded?

`data/search_intent_keywords.csv` contains 48 labeled keyword examples, balanced at 12 examples for each of the four intents. `train_model.py` reads the CSV with pandas and makes a stratified 75/25 train/test split using `random_state=42`.

Preprocessing occurs inside the pipeline's TF-IDF vectorizer: text is lowercased and represented with one-word and two-word features. The logistic-regression classifier is fitted on the training set. The script predicts the held-out test set and prints accuracy plus a classification report.

Finally, Joblib's `dump()` serializes the complete fitted pipeline to `model/intent_model.pkl`, creating the directory if necessary. At runtime, `IntentPredictor.load()` resolves that repository-relative path and loads it with `joblib.load()`. If the artifact does not exist, the API explains how to regenerate it.

Because this is a small demonstration dataset, the reported probability is model confidence on its learned classes, not proof that an intent label is correct for every real-world query.

## 12. How does the system compare the predicted search intent with the actual webpage content to calculate the Search Intent Match score?

The 7-point intent-match category uses predefined cue words for the predicted class. Examples include `guide` and `tutorial` for informational, `best` and `compare` for commercial, `buy` and `download` for transactional, and `login` and `official` for navigational intent.

- Body content earns 3 points for at least three distinct class cues or 1 point for at least one.
- A cue in the title earns 1 point.
- A cue in the meta description earns 1 point.
- Three or more H2s with at least one class cue earn 1 point.
- An expected format/action term in the H1, H2s, or content earns 1 point. For example, commercial pages look for `compare`, `feature`, `benefit`, or `pricing`.

Missing signals generate specific issues and, when the body does not match, a recommendation to reshape the format and copy around the predicted user need. This comparison is rule-based; the ML model predicts the class, while cue matching calculates the page-alignment score.

## 13. How does the project generate critical issues, warnings, passed checks, recommendations, and prioritized SEO actions from an audit?

Each category builds its own issue and recommendation lists while it calculates points. High-impact conditions are also appended to `critical_issues`, including a missing title, meta description, H1, or canonical; severely thin content; a non-indexable page or `noindex`; keyword density above 3%; and an HTTP error status of 400 or higher.

After all categories are scored:

- `warnings` is the flattened category-issue list with exact critical strings removed;
- `passed_checks` contains categories whose score equals their maximum;
- categories are ranked from lowest percentage score to highest, with higher-weight categories winning ties; and
- unique recommendations are collected in that order, up to eight, to form `priority_recommendations`.

The API therefore preserves detailed evidence per category while also producing concise action lists. Some related messages can appear in both critical and warning output when their wording differs, because filtering is based on exact strings.

## 14. How do the HTML, CSS, and JavaScript frontend components communicate with the FastAPI backend to display SEO audit results in the browser dashboard?

FastAPI serves `frontend/templates/index.html` at `/`, mounts `frontend/static/`, and exposes the generated OpenAPI documentation at `/docs`. The HTML form captures every audit input, while `styles.css` provides the responsive visual layout.

On form submission, `frontend/static/app.js`:

1. prevents a normal page reload;
2. reads and normalizes the form controls;
3. builds the same nested JSON structure expected by `SEOAnalysisRequest`;
4. sends it to `/api/analyze` with `fetch()` and `Content-Type: application/json`;
5. parses either the successful result or FastAPI error detail; and
6. renders the overall score, grade, intent, keyword density, progress indicators, 16 category cards, critical issues, warnings, passed checks, and prioritized recommendations.

Dynamic text is escaped before being inserted into generated HTML lists/cards. During a request the submit button is disabled, and failures replace the dashboard with a readable error state.

## 15. How are automated tests and Docker used to improve the reliability, reproducibility, and deployment of the AI SEO Intelligence application?

Pytest covers both the service layer and HTTP API. The current tests verify exact-phrase keyword counting, the 100-point weight total, deterministic repeated results, penalties for missing evidence, grade boundaries, content-gap output, health/frontend/static/Swagger delivery, Pydantic validation, the complete audit response contract, critical issues, intent prediction, and the absence of a history endpoint. FastAPI's `TestClient` exercises routes without starting an external server.

The Dockerfile provides a repeatable Python 3.12 environment. It installs the pinned dependencies from `requirements.txt`, copies the repository, trains the intent model during the image build, exposes port 8000, and starts Uvicorn on `0.0.0.0:8000`. Training at build time ensures that a newly built image contains the required model artifact.

Together, tests help detect scoring and API regressions, while Docker standardizes dependencies, model preparation, and the production start command. The existing suite is focused rather than exhaustive: for example, it does not currently run a browser end-to-end test or build the Docker image in a test.

## Source map

- API setup and frontend delivery: [`app/main.py`](../app/main.py)
- API endpoint flow: [`app/api/routes.py`](../app/api/routes.py)
- Request and response validation: [`app/schemas/seo_schema.py`](../app/schemas/seo_schema.py)
- Audit rules and scoring: [`app/services/seo_analyzer.py`](../app/services/seo_analyzer.py)
- Model loading and prediction: [`app/services/intent_model.py`](../app/services/intent_model.py)
- Model training: [`train_model.py`](../train_model.py)
- Training data: [`data/search_intent_keywords.csv`](../data/search_intent_keywords.csv)
- Browser behavior: [`frontend/static/app.js`](../frontend/static/app.js)
- Automated tests: [`tests/`](../tests)
- Container setup: [`Dockerfile`](../Dockerfile)
