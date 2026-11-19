from typing import Any, Dict, List
from app.schemas import BrandSummary, CompetitorAnalysis


class CompetitorService:
    """
    Normalizes competitor analysis and generates a structured side-by-side
    comparison matrix between the submitted brand and its top competitors.
    """

    def enrich_competitor_section(
        self, brand: BrandSummary, comp_analysis: CompetitorAnalysis
    ) -> Dict[str, Any]:
        comparison_matrix: List[Dict[str, str]] = []
        primary_service = (
            comp_analysis.main_products_and_services[0]
            if comp_analysis.main_products_and_services
            else brand.category
        )
        brand_strength = (
            comp_analysis.brand_competitive_advantages[0]
            if comp_analysis.brand_competitive_advantages
            else "Focused niche value proposition"
        )
        brand_opportunity = (
            comp_analysis.opportunities[0]
            if comp_analysis.opportunities
            else "Expand search visibility and content authority"
        )

        for comp in comp_analysis.competitors:
            comparison_matrix.append(
                {
                    "competitor_name": comp.name,
                    "your_brand": brand.name,
                    "main_service_comparison": f"{primary_service} vs. {comp.main_service}",
                    "target_market": comp.target_market,
                    "your_key_strength": brand_strength,
                    "competitor_key_strength": comp.strengths[0] if comp.strengths else "Established presence",
                    "competitor_gap_to_exploit": (
                        comp.weaknesses_or_gaps[0] if comp.weaknesses_or_gaps else "Limited niche customization"
                    ),
                    "your_opportunity": brand_opportunity,
                    "source_note": comp.source_note,
                }
            )

        result = comp_analysis.model_dump()
        result["side_by_side_comparison"] = comparison_matrix
        return result