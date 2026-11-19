from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from app.utils.validators import UnsafeURLError, validate_public_url


class LinkAnalysisRequest(BaseModel):
    url: str = Field(
        ...,
        description="Public website URL to analyze.",
        examples=["https://www.stripe.com"],
    )

    @field_validator("url")
    @classmethod
    def check_safe_url(cls, value: str) -> str:
        try:
            return validate_public_url(value)
        except UnsafeURLError as exc:
            raise ValueError(str(exc)) from exc


# --- Brand Summary ---
class BrandSummary(BaseModel):
    name: str = Field(..., description="Official brand or company name extracted from the website.")
    category: str = Field(..., description="Main business category or industry vertical.")
    summary: str = Field(..., description="Concise 1-2 sentence overview of what the business does.")


# --- Section 1: Competitor vs Your Brand Details ---
class CompetitorDetail(BaseModel):
    name: str = Field(..., description="Competitor brand name (or clearly labeled AI-suggested competitor).")
    main_service: str = Field(..., description="Primary product or service offered by the competitor.")
    target_market: str = Field(..., description="Competitor's primary target market.")
    strengths: List[str] = Field(..., description="Key strengths of this competitor.")
    weaknesses_or_gaps: List[str] = Field(..., description="Weaknesses or market gaps compared to your brand.")
    source_note: str = Field(
        ...,
        description="Specify 'Verified market competitor' or 'AI-suggested competitor based on category'.",
    )


class CompetitorAnalysis(BaseModel):
    brand_overview: str = Field(..., description="Detailed overview of the submitted brand and its positioning.")
    main_products_and_services: List[str] = Field(..., description="Core products and services offered by the brand.")
    competitors: List[CompetitorDetail] = Field(
        ..., description="At least 3 relevant competitors with strengths and gaps."
    )
    brand_competitive_advantages: List[str] = Field(
        ..., description="Your brand's key competitive advantages over competitors."
    )
    opportunities: List[str] = Field(
        ..., description="Actionable opportunities to improve market positioning."
    )


# --- Section 2: Top 5 Target Search Queries ---
PlatformType = Literal["Google Search", "Facebook", "Instagram", "LinkedIn", "X (Twitter)"]


class TargetSearchQuery(BaseModel):
    query: str = Field(..., description="Relevant search query potential customers use.")
    platforms: List[PlatformType] = Field(
        ...,
        description="Suitable platforms from: Google Search, Facebook, Instagram, LinkedIn, X (Twitter).",
    )
    intent: str = Field(..., description="Search intent (e.g., Service Search, Business Discovery, B2B Search, Inspiration).")
    business_relevance: str = Field(..., description="Why this query is relevant to the business.")
    target_audience: str = Field(..., description="Specific customer segment using this search query.")


# --- Section 3: SEO Improvement ---
class SupportingContentIdea(BaseModel):
    content_type: str = Field(
        ...,
        description="Type of content (e.g., Service Landing Page, Industry Page, FAQ, Blog Topic, Location Page).",
    )
    title_or_topic: str = Field(..., description="Recommended page title or article topic.")
    purpose: str = Field(..., description="How this content improves search visibility and conversions.")


class SEOImprovements(BaseModel):
    primary_keyword: str = Field(..., description="Main target SEO keyword.")
    secondary_keywords: List[str] = Field(..., description="Supporting secondary keywords.")
    long_tail_keywords: List[str] = Field(..., description="Specific high-intent long-tail keywords.")
    relevant_business_keywords: List[str] = Field(..., description="Core industry and brand-related keywords.")
    recommended_title: str = Field(..., description="Optimized SEO title tag (50-60 characters) including primary keyword.")
    title_improvement_notes: str = Field(..., description="Explanation of how the title structure improves upon current page title.")
    meta_description: str = Field(..., description="Compelling meta description (140-160 characters) with relevant keywords.")
    supporting_content: List[SupportingContentIdea] = Field(
        ..., description="Recommended supporting pages, FAQs, and blog topics."
    )


# --- Section 4: Top 5 Services ---
class ServiceItem(BaseModel):
    service_name: str = Field(..., description="Name of the service or product.")
    description: str = Field(..., description="Short explanation of the service.")
    target_industry: str = Field(..., description="Relevant business industry served.")
    target_customer: str = Field(..., description="Potential customer persona or buyer type.")
    main_benefit: str = Field(..., description="Core value or benefit to the customer.")
    extraction_source: Literal["Extracted from website", "Inferred recommendation"] = Field(
        ...,
        description="Whether the service was directly extracted from website content or inferred.",
    )


# --- Section 5: Target Audience Identification ---
class AudienceSegment(BaseModel):
    segment_name: str = Field(..., description="Audience segment label (e.g., Small Businesses, SaaS Startups).")
    business_type: str = Field(..., description="Type of organization or buyer.")
    key_requirement: str = Field(..., description="Primary problem or requirement this audience seeks to solve.")


class TargetAudience(BaseModel):
    primary_audience: List[str] = Field(..., description="Primary target customer segments.")
    secondary_audience: List[str] = Field(..., description="Secondary target customer segments.")
    industry_segments: List[str] = Field(..., description="Key target industries.")
    business_types: List[str] = Field(..., description="Types of businesses targeted (e.g., B2B SMBs, Enterprises, D2C).")
    customer_profiles: List[str] = Field(..., description="Detailed buyer personas and decision-maker roles.")
    geographical_focus: str = Field(..., description="Detected location or geographic market focus (or 'Global / Not specified').")
    customer_needs_and_challenges: List[str] = Field(..., description="Pain points and challenges faced by target customers.")
    customer_interests: List[str] = Field(..., description="Topics, solutions, and outcomes customers care about.")
    recommended_marketing_segments: List[AudienceSegment] = Field(
        ..., description="Structured audience segments prioritized for marketing campaigns."
    )


# --- Complete LLM Output Container ---
class WebsiteAnalysisSections(BaseModel):
    brand: BrandSummary
    competitor_analysis: CompetitorAnalysis
    target_search_queries: List[TargetSearchQuery] = Field(
        ..., description="Exactly 5 high-intent target search queries across supported platforms."
    )
    seo_improvements: SEOImprovements
    top_services: List[ServiceItem] = Field(
        ..., description="Top 5 most important services identified from the website."
    )
    target_audience: TargetAudience


# --- Final API Response ---
class LinkAnalysisResponse(BaseModel):
    success: bool
    website: str
    cached: bool = False
    model_used: str
    brand: BrandSummary
    analysis: dict