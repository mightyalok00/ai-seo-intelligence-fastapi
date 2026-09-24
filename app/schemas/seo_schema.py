from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TechnicalSEOFields(BaseModel):
    """Optional measured technical signals used by the audit."""

    https: Optional[bool] = None
    mobile_friendly: Optional[bool] = None
    page_speed_score: Optional[int] = Field(default=None, ge=0, le=100)
    status_code: Optional[int] = Field(default=None, ge=100, le=599)
    has_viewport: Optional[bool] = None
    has_favicon: Optional[bool] = None
    has_sitemap: Optional[bool] = None
    broken_links: Optional[int] = Field(default=None, ge=0)


class SEOAnalysisRequest(BaseModel):
    """Validated page signals for the strict 100-point SEO audit."""

    keyword: str = Field(..., min_length=2, max_length=120)
    url: str = Field(default="", max_length=2048)
    title: str = Field(default="", max_length=200)
    meta_description: str = Field(default="", max_length=400)
    h1: str = Field(default="", max_length=250)
    h2s: List[str] = Field(default_factory=list, max_length=50)
    content: str = Field(..., min_length=20)
    semantic_terms: List[str] = Field(default_factory=list, max_length=100)
    internal_links: List[str] = Field(default_factory=list, max_length=200)
    external_links: List[str] = Field(default_factory=list, max_length=200)
    image_alts: List[str] = Field(default_factory=list, max_length=200)
    schema_json_ld: Optional[Any] = None
    canonical: str = Field(default="", max_length=2048)
    robots_indexable: Optional[bool] = None
    robots_directives: str = Field(default="", max_length=250)
    technical: TechnicalSEOFields = Field(default_factory=TechnicalSEOFields)

    @field_validator(
        "h2s", "semantic_terms", "internal_links", "external_links", "image_alts"
    )
    @classmethod
    def trim_list_values(cls, values: List[str]) -> List[str]:
        return [value.strip() for value in values]


class ContentGapRequest(BaseModel):
    """Input for comparing two pieces of content."""

    primary_content: str = Field(..., min_length=20)
    competitor_content: str = Field(..., min_length=20)


class KeywordRequest(BaseModel):
    """Input for search-intent prediction."""

    keyword: str = Field(..., min_length=2, max_length=120)


class CategoryScore(BaseModel):
    score: float
    max: int
    issues: List[str]
    recommendations: List[str]


class SEOAnalysisResponse(BaseModel):
    keyword: str
    overall_score: int
    grade: str
    category_scores: Dict[str, CategoryScore]
    critical_issues: List[str]
    warnings: List[str]
    passed_checks: List[str]
    priority_recommendations: List[str]
    search_intent: str
    intent_confidence: float
    keyword_frequency: int
    keyword_density: float
    suggested_title: str
    suggested_meta_description: str
