import re
from typing import Any, Dict, List
import httpx
from bs4 import BeautifulSoup
from app.config import settings
from app.utils.validators import validate_public_url


class WebsiteExtractionError(Exception):
    """Raised when a website cannot be fetched or parsed."""


class WebsiteExtractor:
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async def extract(self, url: str) -> Dict[str, Any]:
        # Re-verify URL safety on redirects too
        safe_url = validate_public_url(url)

        try:
            async with httpx.AsyncClient(
                timeout=settings.request_timeout_seconds,
                follow_redirects=True,
                headers=self.HEADERS,
            ) as client:
                response = await client.get(safe_url)
                # Ensure final redirect destination is also a safe public URL
                validate_public_url(str(response.url))
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise WebsiteExtractionError(
                f"Website returned HTTP {exc.response.status_code} for {safe_url}"
            ) from exc
        except httpx.RequestError as exc:
            raise WebsiteExtractionError(
                f"Unable to connect to {safe_url}: {str(exc)}"
            ) from exc

        content_type = response.headers.get("content-type", "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            raise WebsiteExtractionError(
                f"Unsupported content type '{content_type}'. Expected an HTML webpage."
            )

        return self._parse_html(str(response.url), response.text)

    def _parse_html(self, final_url: str, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")

        # Remove non-content elements to save LLM tokens
        for tag in soup(["script", "style", "noscript", "svg", "iframe", "canvas"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()

        og_site_name = ""
        og_tag = soup.find("meta", attrs={"property": "og:site_name"})
        if og_tag and og_tag.get("content"):
            og_site_name = og_tag["content"].strip()

        meta_keywords = ""
        kw_tag = soup.find("meta", attrs={"name": re.compile(r"^keywords$", re.I)})
        if kw_tag and kw_tag.get("content"):
            meta_keywords = kw_tag["content"].strip()

        # Extract structured headings (H1 - H3)
        headings: List[str] = []
        for h in soup.find_all(["h1", "h2", "h3"]):
            text = " ".join(h.get_text(" ", strip=True).split())
            if text and text not in headings and len(text) <= 160:
                headings.append(text)
            if len(headings) >= 25:
                break

        # Extract clean, deduplicated body text
        raw_lines = [line.strip() for line in soup.get_text(separator="\n").splitlines()]
        seen_lines = set()
        clean_lines: List[str] = []
        for line in raw_lines:
            normalized = " ".join(line.split())
            if len(normalized) < 3:
                continue
            if normalized not in seen_lines:
                seen_lines.add(normalized)
                clean_lines.append(normalized)

        body_text = "\n".join(clean_lines)[: settings.max_extracted_chars]

        return {
            "final_url": final_url,
            "title": title,
            "site_name": og_site_name,
            "meta_description": meta_desc,
            "meta_keywords": meta_keywords,
            "headings": headings,
            "body_text": body_text,
        }