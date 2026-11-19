import time
from typing import Dict, Tuple
from app.config import settings
from app.schemas import LinkAnalysisResponse
from app.services.competitor_service import CompetitorService
from app.services.llm_service import LLMService
from app.services.website_extractor import WebsiteExtractor


class AnalysisService:
    CACHE_TTL_SECONDS = 3600  # Cache identical URL analyses for 1 hour to minimize LLM API costs

    def __init__(self):
        self.extractor = WebsiteExtractor()
        self.llm_service = LLMService()
        self.competitor_service = CompetitorService()
        self._cache: Dict[str, Tuple[float, LinkAnalysisResponse]] = {}

    async def analyze_url(self, url: str) -> LinkAnalysisResponse:
        normalized_key = url.strip().rstrip("/").lower()

        # Return cached result if valid (reduces latency & saves 100% of repeat LLM token costs)
        if normalized_key in self._cache:
            cached_at, cached_response = self._cache[normalized_key]
            if (time.time() - cached_at) < self.CACHE_TTL_SECONDS:
                return cached_response.model_copy(update={"cached": True})
            del self._cache[normalized_key]

        # 1. Fetch and clean website content
        extracted = await self.extractor.extract(url)

        # 2. Analyze extracted content using Gemini Structured Outputs
        sections = await self.llm_service.analyze_website(extracted)

        # 3. Build side-by-side competitor comparison matrix
        enriched_competitors = self.competitor_service.enrich_competitor_section(
            sections.brand, sections.competitor_analysis
        )

        # 4. Assemble final response matching all 5 required sections
        response = LinkAnalysisResponse(
            success=True,
            website=extracted["final_url"],
            cached=False,
            model_used=settings.gemini_model,
            brand=sections.brand,
            analysis={
                "competitor_analysis": enriched_competitors,
                "target_search_queries": [q.model_dump() for q in sections.target_search_queries],
                "seo_improvements": sections.seo_improvements.model_dump(),
                "top_services": [s.model_dump() for s in sections.top_services],
                "target_audience": sections.target_audience.model_dump(),
            },
        )

        self._cache[normalized_key] = (time.time(), response)
        return response