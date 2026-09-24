import json
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are",
    "was", "were", "have", "has", "had", "but", "not", "into", "about", "how",
    "what", "when", "where", "why", "who", "can", "will", "our", "their", "they",
    "its", "a", "an", "of", "to", "in", "on", "is", "be", "as", "at", "or", "by",
}

CATEGORY_WEIGHTS = {
    "title": 8,
    "meta_description": 7,
    "h1_h2_structure": 7,
    "content_depth": 10,
    "semantic_terms": 8,
    "internal_links": 6,
    "external_links": 4,
    "image_alt": 5,
    "schema": 6,
    "canonical": 4,
    "robots_indexability": 6,
    "keyword_usage_stuffing": 7,
    "readability": 6,
    "search_intent_match": 7,
    "url_quality": 4,
    "technical_checks": 5,
}

INTENT_CUES = {
    "informational": {"guide", "how", "what", "why", "learn", "tips", "tutorial", "examples"},
    "commercial": {"best", "review", "compare", "comparison", "top", "versus", "features", "pricing"},
    "transactional": {"buy", "order", "download", "book", "subscribe", "deal", "price", "get"},
    "navigational": {"login", "official", "website", "portal", "account", "support", "contact", "dashboard"},
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9']+", _normalize(text))


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_phrase = _normalize(phrase)
    if not normalized_phrase:
        return False
    return re.search(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)", _normalize(text)) is not None


def _category(score: float, maximum: int, issues: List[str], recommendations: List[str]) -> Dict:
    return {
        "score": round(max(0, min(maximum, score)), 1),
        "max": maximum,
        "issues": issues,
        "recommendations": recommendations,
    }


def _valid_http_url(value: str) -> bool:
    parsed = urlparse((value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _syllables(word: str) -> int:
    groups = re.findall(r"[aeiouy]+", word.lower())
    count = len(groups)
    if word.lower().endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def keyword_metrics(keyword: str, content: str) -> Dict[str, float]:
    """Return exact-phrase frequency and density as a percentage of content words."""
    keyword_norm = _normalize(keyword)
    content_norm = _normalize(content)
    pattern = rf"(?<!\w){re.escape(keyword_norm)}(?!\w)" if keyword_norm else r"(?!x)x"
    frequency = len(re.findall(pattern, content_norm))
    word_count = max(len(_tokens(content)), 1)
    keyword_word_count = max(len(_tokens(keyword)), 1)
    density = (frequency * keyword_word_count / word_count) * 100
    return {
        "frequency": frequency,
        "density": round(density, 2),
        "word_count": word_count,
    }


def grade_for_score(score: int) -> str:
    if score >= 90:
        return "Exceptional"
    if score >= 80:
        return "Strong"
    if score >= 70:
        return "Good but needs improvement"
    if score >= 60:
        return "Average"
    if score >= 40:
        return "Weak"
    return "Poor"


def _parse_schema(value: Any) -> Optional[Any]:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return False
    return value


def analyze_seo(
    *,
    keyword: str,
    url: str = "",
    title: str = "",
    meta_description: str = "",
    h1: str = "",
    h2s: Optional[List[str]] = None,
    content: str,
    semantic_terms: Optional[List[str]] = None,
    internal_links: Optional[List[str]] = None,
    external_links: Optional[List[str]] = None,
    image_alts: Optional[List[str]] = None,
    schema_json_ld: Any = None,
    canonical: str = "",
    robots_indexable: Optional[bool] = None,
    robots_directives: str = "",
    technical: Optional[Dict] = None,
    predicted_intent: str = "informational",
) -> Dict:
    """Run a strict, deterministic 16-category audit worth exactly 100 points."""
    h2s = [item.strip() for item in (h2s or []) if item.strip()]
    semantic_terms = [item.strip() for item in (semantic_terms or []) if item.strip()]
    internal_links = [item.strip() for item in (internal_links or []) if item.strip()]
    external_links = [item.strip() for item in (external_links or []) if item.strip()]
    image_alts = [item.strip() for item in (image_alts or [])]
    technical = technical or {}
    metrics = keyword_metrics(keyword, content)
    keyword_n = _normalize(keyword)
    content_n = _normalize(content)
    all_headings = " ".join([h1, *h2s])
    categories: Dict[str, Dict] = {}
    passed: List[str] = []
    critical: List[str] = []

    # Title: 8 points.
    issues: List[str] = []
    recs: List[str] = []
    score = 0
    title_clean = title.strip()
    if not title_clean:
        issues.append("The title is missing.")
        recs.append("Add a unique, descriptive title containing the target keyword.")
        critical.append("Missing page title")
    else:
        score += 1
        if _contains_phrase(title_clean, keyword):
            score += 2
            if _normalize(title_clean).startswith(keyword_n):
                score += 1
            else:
                issues.append("The target keyword is not near the start of the title.")
                recs.append("Move the keyword closer to the beginning when it reads naturally.")
        else:
            issues.append("The title does not contain the exact target keyword.")
            recs.append("Use the target keyword once in the title.")
        length = len(title_clean)
        if 50 <= length <= 60:
            score += 2
        elif 40 <= length <= 69:
            score += 1
            issues.append(f"Title length is acceptable but not ideal ({length} characters).")
        else:
            issues.append(f"Title length is outside the useful 40–69 range ({length} characters).")
            recs.append("Aim for a concise 50–60 character title.")
        title_words = _tokens(title_clean)
        if title_words and max(Counter(title_words).values()) <= 2 and title_clean.count("!") <= 1:
            score += 1
        else:
            issues.append("The title contains repetitive or overly promotional wording.")
        if any(cue in set(title_words) for cue in INTENT_CUES.get(predicted_intent, set())):
            score += 1
        else:
            issues.append(f"The title gives a weak {predicted_intent} intent signal.")
            recs.append(f"Make the title clearly support {predicted_intent} search intent.")
    categories["title"] = _category(score, 8, issues, recs)

    # Meta description: 7 points.
    issues, recs, score = [], [], 0
    meta = meta_description.strip()
    if not meta:
        issues.append("The meta description is missing.")
        recs.append("Write a unique 140–160 character summary with the keyword and a clear benefit.")
        critical.append("Missing meta description")
    else:
        score += 1
        meta_len = len(meta)
        if 140 <= meta_len <= 160:
            score += 2
        elif 120 <= meta_len <= 170:
            score += 1
            issues.append(f"Meta description length is acceptable but not ideal ({meta_len} characters).")
        else:
            issues.append(f"Meta description length is outside 120–170 characters ({meta_len}).")
            recs.append("Rewrite it to approximately 140–160 characters.")
        if _contains_phrase(meta, keyword):
            score += 1
        else:
            issues.append("The meta description omits the exact target keyword.")
            recs.append("Include the keyword naturally once.")
        meta_words = set(_tokens(meta))
        if any(cue in meta_words for cue in INTENT_CUES.get(predicted_intent, set())):
            score += 1
        else:
            issues.append("The meta description does not clearly reinforce search intent.")
        if any(word in meta_words for word in {"discover", "learn", "compare", "get", "find", "explore", "choose"}):
            score += 1
        else:
            issues.append("The meta description lacks a clear action or benefit.")
            recs.append("Add a specific benefit and natural call to action.")
        if keyword_metrics(keyword, meta)["density"] <= 4 and _normalize(meta) != _normalize(title):
            score += 1
        else:
            issues.append("The meta description is repetitive, duplicated, or keyword-heavy.")
    categories["meta_description"] = _category(score, 7, issues, recs)

    # H1/H2 structure: 7 points.
    issues, recs, score = [], [], 0
    if h1.strip():
        score += 1
        if _contains_phrase(h1, keyword):
            score += 2
        else:
            issues.append("The H1 does not contain the target keyword.")
            recs.append("Use the keyword naturally in the single H1.")
        if _normalize(h1) != _normalize(title):
            score += 1
        else:
            issues.append("The H1 exactly duplicates the title.")
            recs.append("Make the H1 complementary rather than identical to the title.")
    else:
        issues.append("The H1 is missing.")
        recs.append("Add one descriptive H1 containing the target keyword.")
        critical.append("Missing H1 heading")
    if len(h2s) >= 3:
        score += 2
    elif len(h2s) >= 1:
        score += 1
        issues.append("The page has too few H2 sections for strong topical structure.")
        recs.append("Use at least three useful H2 sections.")
    else:
        issues.append("No H2 sections were supplied.")
        recs.append("Break the content into at least three descriptive H2 sections.")
    heading_terms = sum(1 for term in semantic_terms if _contains_phrase(all_headings, term))
    if semantic_terms and heading_terms >= min(2, len(semantic_terms)):
        score += 1
    else:
        issues.append("H2s show limited semantic topic coverage.")
        recs.append("Use relevant related terms in descriptive H2s without forcing them.")
    categories["h1_h2_structure"] = _category(score, 7, issues, recs)

    # Content depth: 10 points.
    issues, recs, score = [], [], 0
    words = metrics["word_count"]
    if words >= 1500:
        score += 5
    elif words >= 1000:
        score += 4
    elif words >= 700:
        score += 3
    elif words >= 400:
        score += 2
    elif words >= 200:
        score += 1
    else:
        issues.append(f"Content is very thin ({words} words).")
    if words < 1000:
        recs.append("Expand the page with original, useful coverage where the topic warrants it.")
        if words < 200:
            critical.append("Severely thin content")
    if _contains_phrase(" ".join(_tokens(content)[:100]), keyword):
        score += 1
    else:
        issues.append("The main topic is not established in the first 100 words.")
        recs.append("Introduce the target topic early and naturally.")
    sentences = [s.strip() for s in re.split(r"[.!?]+", content) if _tokens(s)]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    if len(sentences) >= 12:
        score += 1
    else:
        issues.append("Content development is limited by a low sentence count.")
    if len(paragraphs) >= 4 or (len(sentences) >= 16 and len(h2s) >= 3):
        score += 1
    else:
        issues.append("The content needs clearer sections or paragraph structure.")
    semantic_hits = sum(1 for term in semantic_terms if _contains_phrase(content, term))
    coverage = semantic_hits / len(semantic_terms) if semantic_terms else 0
    if semantic_terms and coverage >= 0.8 and semantic_hits >= 5:
        score += 2
    elif semantic_terms and coverage >= 0.5:
        score += 1
    else:
        issues.append("The content lacks enough supplied related-topic coverage.")
    categories["content_depth"] = _category(score, 10, issues, recs)

    # Semantic terms: 8 points.
    issues, recs, score = [], [], 0
    if not semantic_terms:
        issues.append("No semantic or related terms were supplied for comparison.")
        recs.append("Provide a researched list of related entities, subtopics, and natural variants.")
    else:
        unique_terms = list(dict.fromkeys(_normalize(term) for term in semantic_terms))
        hits = [term for term in unique_terms if _contains_phrase(content, term)]
        ratio = len(hits) / len(unique_terms)
        score += min(5, math.floor(ratio * 6))
        if len(unique_terms) >= 8:
            score += 2
        elif len(unique_terms) >= 4:
            score += 1
        else:
            issues.append("The semantic-term set is too small to demonstrate topical breadth.")
        if any(_contains_phrase(all_headings, term) for term in hits):
            score += 1
        else:
            issues.append("Covered semantic terms do not appear in headings.")
        missing_terms = [term for term in unique_terms if term not in hits]
        if missing_terms:
            issues.append(f"Missing related terms: {', '.join(missing_terms[:5])}.")
            recs.append("Add only relevant missing concepts where they improve the answer.")
    categories["semantic_terms"] = _category(score, 8, issues, recs)

    # Internal links: 6 points.
    issues, recs, score = [], [], 0
    valid_internal = [link for link in internal_links if link.startswith("/") or _valid_http_url(link)]
    if len(valid_internal) >= 5:
        score += 4
    elif len(valid_internal) >= 3:
        score += 3
    elif len(valid_internal) >= 1:
        score += 1
    else:
        issues.append("No valid internal links were supplied.")
        recs.append("Add contextual links to relevant pages in the same site.")
    if valid_internal and len(valid_internal) == len(internal_links):
        score += 1
    elif internal_links:
        issues.append("Some internal links are malformed.")
    internal_paths = {urlparse(link).path.rstrip("/") for link in valid_internal}
    if len(internal_paths) >= 4:
        score += 1
    else:
        issues.append("Internal links have limited destination diversity.")
    categories["internal_links"] = _category(score, 6, issues, recs)

    # External links: 4 points.
    issues, recs, score = [], [], 0
    valid_external = [link for link in external_links if _valid_http_url(link)]
    if len(valid_external) >= 2:
        score += 2
    elif len(valid_external) == 1:
        score += 1
    else:
        issues.append("No valid external citations were supplied.")
        recs.append("Cite authoritative primary sources where external support is useful.")
    if valid_external and all(urlparse(link).scheme == "https" for link in valid_external):
        score += 1
    elif valid_external:
        issues.append("Not every external link uses HTTPS.")
    domains = {urlparse(link).netloc.lower().removeprefix("www.") for link in valid_external}
    if len(domains) >= 2:
        score += 1
    else:
        issues.append("External source diversity is limited.")
    categories["external_links"] = _category(score, 4, issues, recs)

    # Image ALT: 5 points.
    issues, recs, score = [], [], 0
    nonempty_alts = [alt for alt in image_alts if alt]
    if not image_alts:
        issues.append("No image ALT audit data was supplied.")
        recs.append("List each content image's ALT text, using an empty line for a missing ALT.")
    else:
        coverage = len(nonempty_alts) / len(image_alts)
        score += 2 if coverage == 1 else 1 if coverage >= 0.8 else 0
        if coverage < 1:
            issues.append(f"{len(image_alts) - len(nonempty_alts)} image(s) have missing ALT text.")
        descriptive = [alt for alt in nonempty_alts if 5 <= len(_tokens(alt)) <= 15]
        if nonempty_alts and len(descriptive) == len(nonempty_alts):
            score += 2
        elif descriptive:
            score += 1
            issues.append("Some ALT text is too vague or excessively long.")
        else:
            issues.append("ALT text is not sufficiently descriptive.")
        if len(nonempty_alts) >= 3 and any(
            _contains_phrase(alt, keyword) or any(_contains_phrase(alt, term) for term in semantic_terms)
            for alt in nonempty_alts
        ):
            score += 1
        else:
            issues.append("Image ALT text shows weak topical relevance or too little sample data.")
    categories["image_alt"] = _category(score, 5, issues, recs)

    # Schema: 6 points.
    issues, recs, score = [], [], 0
    schema = _parse_schema(schema_json_ld)
    if schema is None:
        issues.append("JSON-LD schema is missing.")
        recs.append("Add valid, page-specific JSON-LD using an appropriate Schema.org type.")
    elif schema is False or not isinstance(schema, (dict, list)):
        issues.append("Schema JSON-LD is invalid JSON or has the wrong shape.")
        recs.append("Validate the JSON-LD and provide an object or array of objects.")
    else:
        score += 1
        nodes = schema if isinstance(schema, list) else [schema]
        if all(isinstance(node, dict) and node.get("@context") for node in nodes):
            score += 1
        else:
            issues.append("Schema is missing @context.")
        types = [node.get("@type") for node in nodes if isinstance(node, dict) and node.get("@type")]
        if types:
            score += 1
            recognized = {"Article", "BlogPosting", "Product", "Service", "FAQPage", "HowTo", "WebPage", "Organization", "LocalBusiness"}
            if any(schema_type in recognized for schema_type in types):
                score += 1
            else:
                issues.append("Schema type is present but not one of the audit's common page types.")
        else:
            issues.append("Schema is missing @type.")
        rich_nodes = [node for node in nodes if isinstance(node, dict) and len(node) >= 5]
        if rich_nodes:
            score += 1
        else:
            issues.append("Schema has too few page-specific properties.")
        if len(nodes) >= 2 or any(
            isinstance(node, dict) and any(key in node for key in ("headline", "name", "mainEntity", "offers"))
            for node in nodes
        ):
            score += 1
        else:
            issues.append("Schema lacks a useful primary entity property.")
    categories["schema"] = _category(score, 6, issues, recs)

    # Canonical: 4 points.
    issues, recs, score = [], [], 0
    if canonical.strip():
        score += 1
        if _valid_http_url(canonical):
            score += 1
            if _valid_http_url(url) and urlparse(canonical).netloc.lower() == urlparse(url).netloc.lower():
                score += 1
            else:
                issues.append("Canonical host cannot be confirmed against the audited URL.")
            if _valid_http_url(url) and canonical.rstrip("/") == url.rstrip("/"):
                score += 1
            else:
                issues.append("Canonical is not an exact self-reference for the audited URL.")
        else:
            issues.append("Canonical is not a valid absolute HTTP(S) URL.")
    else:
        issues.append("Canonical URL is missing.")
        recs.append("Add one valid self-referencing canonical URL.")
        critical.append("Missing canonical URL")
    categories["canonical"] = _category(score, 4, issues, recs)

    # Robots/indexability: 6 points.
    issues, recs, score = [], [], 0
    directives = {part.strip().lower() for part in robots_directives.split(",") if part.strip()}
    if robots_indexable is True:
        score += 3
    elif robots_indexable is False:
        issues.append("The page is marked non-indexable.")
        recs.append("Remove unintended blocking signals before publishing.")
        critical.append("Page is not indexable")
    else:
        issues.append("Indexability was not explicitly confirmed.")
        recs.append("Confirm the live page is indexable in robots rules and response headers.")
    if directives:
        score += 1
        if "noindex" not in directives and "nofollow" not in directives:
            score += 1
            if "index" in directives and "follow" in directives:
                score += 1
            else:
                issues.append("Robots directives do not explicitly state index, follow.")
        else:
            issues.append("Robots directives contain noindex or nofollow.")
            if "noindex" in directives and "Page is not indexable" not in critical:
                critical.append("Robots meta contains noindex")
    else:
        issues.append("Robots directives were not supplied.")
    categories["robots_indexability"] = _category(score, 6, issues, recs)

    # Keyword usage/stuffing: 7 points.
    issues, recs, score = [], [], 0
    density = metrics["density"]
    frequency = metrics["frequency"]
    if 0.5 <= density <= 1.5:
        score += 3
    elif 0.2 <= density <= 2.5:
        score += 2
        issues.append(f"Keyword density is acceptable but not in the conservative ideal band ({density}%).")
    elif 0 < density <= 3.0:
        score += 1
        issues.append(f"Keyword density is approaching an unnatural level ({density}%).")
    elif density > 3.0:
        issues.append(f"Keyword density suggests stuffing ({density}%).")
        recs.append("Remove repetitive exact-match uses and write naturally.")
        critical.append("Possible keyword stuffing")
    else:
        issues.append("The exact target keyword is absent from the content.")
        recs.append("Use the target keyword naturally in the body copy.")
    if frequency >= 2:
        score += 1
    elif frequency == 1:
        issues.append("The target keyword appears only once.")
    if _contains_phrase(" ".join(_tokens(content)[:100]), keyword):
        score += 1
    else:
        issues.append("The keyword is absent from the opening 100 words.")
    content_tokens = _tokens(content)
    thirds = [content_tokens[i * len(content_tokens) // 3:(i + 1) * len(content_tokens) // 3] for i in range(3)]
    if all(_contains_phrase(" ".join(part), keyword) for part in thirds):
        score += 1
    else:
        issues.append("Exact-match keyword usage is not distributed across the page.")
    repeated = re.search(rf"(?:{re.escape(keyword_n)}[\s,.;:!-]*){{3,}}", content_n)
    if not repeated:
        score += 1
    else:
        issues.append("Repeated adjacent keyword use appears unnatural.")
    categories["keyword_usage_stuffing"] = _category(score, 7, issues, recs)

    # Readability: 6 points.
    issues, recs, score = [], [], 0
    tokens = _tokens(content)
    sentence_count = max(len(sentences), 1)
    syllable_count = sum(_syllables(word) for word in tokens)
    flesch = 206.835 - (1.015 * len(tokens) / sentence_count) - (84.6 * syllable_count / max(len(tokens), 1))
    if 55 <= flesch <= 75:
        score += 3
    elif 40 <= flesch < 85:
        score += 2
        issues.append(f"Readability is usable but outside the audit's ideal range (Flesch {round(flesch)}).")
    elif 25 <= flesch < 95:
        score += 1
        issues.append(f"Readability may be too difficult or overly simple (Flesch {round(flesch)}).")
    else:
        issues.append(f"Readability is outside a practical range (Flesch {round(flesch)}).")
    average_sentence = len(tokens) / sentence_count
    if 12 <= average_sentence <= 20:
        score += 1
    else:
        issues.append(f"Average sentence length is {round(average_sentence, 1)} words.")
        recs.append("Use varied sentences averaging roughly 12–20 words.")
    if len(paragraphs) >= 4 or (len(sentences) >= 12 and len(h2s) >= 3):
        score += 1
    else:
        issues.append("The page needs more scannable paragraph or section breaks.")
    long_word_ratio = sum(1 for word in tokens if len(word) >= 12) / max(len(tokens), 1)
    if long_word_ratio <= 0.08:
        score += 1
    else:
        issues.append("Long-word usage is high for general web readability.")
    categories["readability"] = _category(score, 6, issues, recs)

    # Search intent match: 7 points.
    issues, recs, score = [], [], 0
    cues = INTENT_CUES.get(predicted_intent, set())
    title_cues = cues.intersection(_tokens(title))
    meta_cues = cues.intersection(_tokens(meta_description))
    content_cues = cues.intersection(_tokens(content))
    if len(content_cues) >= 3:
        score += 3
    elif len(content_cues) >= 1:
        score += 1
        issues.append("The body provides only weak signals for the predicted search intent.")
    else:
        issues.append(f"The body does not clearly match {predicted_intent} intent.")
        recs.append(f"Shape the page format and copy around {predicted_intent} user needs.")
    if title_cues:
        score += 1
    else:
        issues.append("The title does not signal the predicted intent.")
    if meta_cues:
        score += 1
    else:
        issues.append("The meta description does not signal the predicted intent.")
    if len(h2s) >= 3 and any(cues.intersection(_tokens(heading)) for heading in h2s):
        score += 1
    else:
        issues.append("The heading structure does not strongly support the predicted intent.")
    intent_action_terms = {
        "informational": {"answer", "example", "step", "guide"},
        "commercial": {"compare", "feature", "benefit", "pricing"},
        "transactional": {"buy", "order", "book", "download"},
        "navigational": {"login", "contact", "support", "official"},
    }.get(predicted_intent, set())
    if intent_action_terms.intersection(_tokens(" ".join([h1, *h2s, content]))):
        score += 1
    else:
        issues.append("The page lacks the expected format/action for this intent.")
    categories["search_intent_match"] = _category(score, 7, issues, recs)

    # URL quality: 4 points.
    issues, recs, score = [], [], 0
    if url.strip():
        score += 1
        if _valid_http_url(url):
            score += 1
            parsed = urlparse(url)
            slug = parsed.path.strip("/").replace("-", " ")
            if _contains_phrase(slug, keyword) or all(token in _tokens(slug) for token in _tokens(keyword)):
                score += 1
            else:
                issues.append("The URL slug does not clearly reflect the target keyword.")
            clean_path = bool(parsed.path) and not re.search(r"[_A-Z]|\d{5,}|//", parsed.path) and not parsed.query
            if clean_path and len(url) <= 100:
                score += 1
            else:
                issues.append("The URL is long, parameterized, or not cleanly formatted.")
        else:
            issues.append("The audited URL is not a valid absolute HTTP(S) URL.")
    else:
        issues.append("The page URL is missing.")
        recs.append("Supply a short, descriptive HTTPS URL with a readable keyword-focused slug.")
    categories["url_quality"] = _category(score, 4, issues, recs)

    # Technical checks: 5 points.
    issues, recs, score = [], [], 0
    https_value = technical.get("https")
    if https_value is True or (_valid_http_url(url) and urlparse(url).scheme == "https"):
        score += 1
    else:
        issues.append("HTTPS was not confirmed.")
    status_code = technical.get("status_code")
    if status_code == 200:
        score += 1
    elif status_code is not None:
        issues.append(f"The supplied HTTP status is {status_code}, not 200.")
        if int(status_code) >= 400:
            critical.append(f"Page returns HTTP {status_code}")
    else:
        issues.append("HTTP status was not supplied.")
    if technical.get("mobile_friendly") is True and technical.get("has_viewport") is True:
        score += 1
    else:
        issues.append("Mobile friendliness and viewport configuration were not both confirmed.")
    speed = technical.get("page_speed_score")
    if speed is not None and speed >= 90:
        score += 1
    elif speed is not None and speed >= 70:
        score += 0.5
        issues.append(f"Page speed is acceptable but below 90 ({speed}).")
    else:
        issues.append("Page speed of 90+ was not confirmed.")
    if (
        technical.get("has_favicon") is True
        and technical.get("has_sitemap") is True
        and technical.get("broken_links") == 0
    ):
        score += 1
    else:
        issues.append("Favicon, sitemap, and zero broken links were not all confirmed.")
        recs.append("Confirm a favicon, discoverable sitemap, and no broken links.")
    categories["technical_checks"] = _category(score, 5, issues, recs)

    overall_score = int(round(sum(item["score"] for item in categories.values())))
    overall_score = max(0, min(100, overall_score))
    warnings = [issue for item in categories.values() for issue in item["issues"] if issue not in critical]
    for name, item in categories.items():
        if item["score"] == item["max"]:
            passed.append(f"{name.replace('_', ' ').title()}: all strict checks passed.")
    ranked = sorted(
        categories.items(),
        key=lambda pair: (pair[1]["score"] / pair[1]["max"], -pair[1]["max"]),
    )
    priority: List[str] = []
    for _, item in ranked:
        for recommendation in item["recommendations"]:
            if recommendation not in priority:
                priority.append(recommendation)
            if len(priority) == 8:
                break
        if len(priority) == 8:
            break

    return {
        "overall_score": overall_score,
        "grade": grade_for_score(overall_score),
        "category_scores": categories,
        "critical_issues": list(dict.fromkeys(critical)),
        "warnings": warnings,
        "passed_checks": passed,
        "priority_recommendations": priority,
        "keyword_frequency": metrics["frequency"],
        "keyword_density": metrics["density"],
    }


def suggest_title(keyword: str) -> str:
    """Template-based title suggestion; no paid LLM is required."""
    clean = keyword.strip().title()
    return f"{clean}: Practical Guide, Tips & Best Practices"


def suggest_meta_description(keyword: str) -> str:
    """Template-based SEO meta-description suggestion."""
    clean = keyword.strip()
    text = (
        f"Learn about {clean}, key best practices, practical tips, and important factors "
        f"to consider so you can make better-informed decisions."
    )
    return text[:160].rstrip()


def content_gap(primary_content: str, competitor_content: str) -> List[str]:
    """Return useful competitor terms not present in the primary content."""
    primary = {token for token in _tokens(primary_content) if len(token) > 3 and token not in STOPWORDS}
    competitor_tokens = [
        token for token in _tokens(competitor_content) if len(token) > 3 and token not in STOPWORDS
    ]
    counts = Counter(competitor_tokens)
    missing = [word for word, _ in counts.most_common() if word not in primary]
    return missing[:20]
