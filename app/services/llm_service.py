import json
from typing import Any, Dict
from google import genai
from google.genai import types
from app.config import settings
from app.schemas import WebsiteAnalysisSections


class LLMAnalysisError(Exception):
    """Raised when the LLM call fails or returns invalid data."""


class LLMService:
    def __init__(self):
        self.model_name = settings.gemini_model
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    async def analyze_website(self, extracted_data: Dict[str, Any]) -> WebsiteAnalysisSections:
        if not self.client or "your_gemini_api_key" in settings.gemini_api_key:
            raise LLMAnalysisError(
                "Missing or invalid GEMINI_API_KEY. Please configure it in your .env file."
            )

        prompt = self._build_prompt(extracted_data)

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are an expert business strategist, competitive intelligence analyst, and technical SEO specialist. "
                        "Analyze ONLY the provided website content accurately. "
                        "STRICT RULES:\n"
                        "1. Base brand, services, and audience strictly on actual extracted website content. Clearly label any inferred services as 'Inferred recommendation'.\n"
                        "2. Identify at least 3 relevant competitors. If a competitor is not explicitly verified from the site text, mark its source_note as 'AI-suggested competitor based on category'.\n"
                        "3. Generate exactly 5 target search queries mapped to valid platforms (Google Search, Facebook, Instagram, LinkedIn, X (Twitter)). NEVER invent search volumes or ranking metrics.\n"
                        "4. Provide practical, concrete SEO improvements (keywords, optimized 50-60 char title, 140-160 char meta description, and supporting content ideas)."
                    ),
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=WebsiteAnalysisSections,
                ),
            )
        except Exception as exc:
            raise LLMAnalysisError(f"Gemini API request failed: {str(exc)}") from exc

        if not response.text:
            raise LLMAnalysisError("LLM returned an empty response.")

        try:
            parsed_json = json.loads(response.text)
            return WebsiteAnalysisSections.model_validate(parsed_json)
        except Exception as exc:
            raise LLMAnalysisError(f"Failed to validate structured LLM output: {str(exc)}") from exc

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        headings_str = "\n- ".join(data.get("headings", [])) or "None detected"
        return (
            f"Analyze the following website and generate all 5 structured business & SEO analysis sections:\n\n"
            f"URL: {data.get('final_url')}\n"
            f"Page Title: {data.get('title') or 'N/A'}\n"
            f"Site Name: {data.get('site_name') or 'N/A'}\n"
            f"Meta Description: {data.get('meta_description') or 'N/A'}\n"
            f"Meta Keywords: {data.get('meta_keywords') or 'N/A'}\n\n"
            f"Key Headings (H1-H3):\n- {headings_str}\n\n"
            f"Extracted Page Content:\n{data.get('body_text', '')}\n"
        )