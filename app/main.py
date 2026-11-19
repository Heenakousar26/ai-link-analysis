from fastapi import FastAPI, HTTPException
from app.config import settings
from app.schemas import LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.llm_service import LLMAnalysisError
from app.services.website_extractor import WebsiteExtractionError
from app.utils.validators import UnsafeURLError

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-Powered REST API that fetches website content, extracts clean business signals, "
        "and generates structured Competitor, Search Query, SEO, Services, and Target Audience insights."
    ),
    version="1.0.0",
)

analysis_service = AnalysisService()


@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "running",
        "service": settings.app_name,
        "model": settings.gemini_model,
        "docs": "/docs",
    }


@app.post("/link-analysis", response_model=LinkAnalysisResponse, tags=["Link Analysis"])
async def analyze_website_link(payload: LinkAnalysisRequest) -> LinkAnalysisResponse:
    """
    Validate a public URL (with SSRF protection), extract website content,
    and generate a 5-section structured business & SEO analysis using Gemini.
    """
    try:
        return await analysis_service.analyze_url(payload.url)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WebsiteExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMAnalysisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc