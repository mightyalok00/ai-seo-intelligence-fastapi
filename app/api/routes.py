from fastapi import APIRouter, HTTPException

from app.schemas.seo_schema import (
    ContentGapRequest,
    KeywordRequest,
    SEOAnalysisRequest,
    SEOAnalysisResponse,
)
from app.services.intent_model import intent_predictor
from app.services.seo_analyzer import (
    analyze_seo,
    content_gap,
    suggest_meta_description,
    suggest_title,
)


router = APIRouter()


@router.get("/health")
def health():
    """Simple health endpoint for uptime checks."""
    return {"status": "ok", "service": "AI SEO Intelligence API"}


@router.post("/predict-intent")
def predict_intent(payload: KeywordRequest):
    """Predict one of four common search-intent classes."""
    try:
        intent, confidence = intent_predictor.predict(payload.keyword)
        return {
            "keyword": payload.keyword,
            "search_intent": intent,
            "confidence": confidence,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/analyze", response_model=SEOAnalysisResponse)
def analyze(payload: SEOAnalysisRequest):
    """Run complete SEO analysis, intent prediction, suggestions and persistence."""
    try:
        intent, confidence = intent_predictor.predict(payload.keyword)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    base = analyze_seo(
        keyword=payload.keyword,
        url=payload.url,
        title=payload.title,
        meta_description=payload.meta_description,
        h1=payload.h1,
        h2s=payload.h2s,
        content=payload.content,
        semantic_terms=payload.semantic_terms,
        internal_links=payload.internal_links,
        external_links=payload.external_links,
        image_alts=payload.image_alts,
        schema_json_ld=payload.schema_json_ld,
        canonical=payload.canonical,
        robots_indexable=payload.robots_indexable,
        robots_directives=payload.robots_directives,
        technical=payload.technical.model_dump(),
        predicted_intent=intent,
    )

    result = {
        "keyword": payload.keyword,
        **base,
        "search_intent": intent,
        "intent_confidence": confidence,
        "suggested_title": suggest_title(payload.keyword),
        "suggested_meta_description": suggest_meta_description(payload.keyword),
    }

    return result


@router.post("/content-gap")
def compare_content(payload: ContentGapRequest):
    """Find high-frequency terms in competitor content missing from primary content."""
    missing_topics = content_gap(
        payload.primary_content,
        payload.competitor_content,
    )
    return {
        "missing_topics": missing_topics,
        "count": len(missing_topics),
    }
