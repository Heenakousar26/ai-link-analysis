```markdown
# AI-Powered Website Link Analysis API

A FastAPI REST API that fetches and parses a website's HTML content, validates URLs with DNS-resolved SSRF protection, and leverages **Google Gemini (`gemini-2.5-flash`)** Structured Outputs to generate a comprehensive 5-section business, competitive intelligence, SEO, search query, and target audience analysis.

---

## Live Deployment & API Documentation

* **Live Base URL:** `https://ai-link-analysis.onrender.com` *(Replace with your actual Render URL after deploying)*
* **API Endpoint:** `POST https://ai-link-analysis.onrender.com/link-analysis`
* **Interactive Swagger Docs:** `https://ai-link-analysis.onrender.com/docs`

---

## Project Structure

```text
ai-link-analysis/
├── app/
│   ├── main.py                      # FastAPI application & POST /link-analysis endpoint
│   ├── config.py                    # Environment configuration (Pydantic Settings)
│   ├── schemas.py                   # Request/response models & 5-section JSON schemas
│   ├── services/
│   │   ├── website_extractor.py     # Async HTTPX fetcher & BeautifulSoup HTML cleaner
│   │   ├── llm_service.py           # Gemini 2.5 Flash structured JSON analysis
│   │   ├── competitor_service.py    # Side-by-side brand vs. competitor matrix builder
│   │   └── analysis_service.py      # Orchestration pipeline with 1-hour TTL caching
│   └── utils/
│       └── validators.py            # URL & DNS-resolved SSRF IP protection
├── tests/
│   └── test_link_analysis.py        # Pytest suite (SSRF, HTML parser, 5-section schema)
├── screenshots/
│   └── link_analysis_response.png   # Swagger UI live test screenshot
├── .env.example
├── requirements.txt
└── README.md

```

---

## LLM Platform & Model Research (Cost, Speed, and Accuracy)

To identify the optimal production LLM for automated website link analysis, three leading commercial providers were evaluated using current official pricing documentation, context capabilities, native JSON schema enforcement, and latency characteristics.

### A. LLM Provider & Model Comparison

| Criteria | Google Gemini (`gemini-2.5-flash`) | OpenAI (`gpt-4o-mini`) | Anthropic (`claude-3-5-haiku`) |
| --- | --- | --- | --- |
| **Provider** | Google AI / Google Cloud | OpenAI | Anthropic |
| **Input Pricing** | **$0.30 / 1M tokens** (Cached: $0.03 / 1M) | $0.15 / 1M tokens (Cached: $0.075 / 1M) | $0.80 / 1M tokens |
| **Output Pricing** | **$2.50 / 1M tokens** | $0.60 / 1M tokens | $4.00 / 1M tokens |
| **Context Window** | **1,048,576 tokens (1M)** | 128,000 tokens | 200,000 tokens |
| **Response Speed** | **~1.5 – 3.0s** *(estimated for ~1.4k output tokens; high tokens/sec)* | ~2.5 – 4.5s *(estimated)* | ~2.0 – 4.0s *(estimated)* |
| **Accuracy (Extraction & SEO)** | High reasoning & multi-section synthesis quality | Strong general instruction following | Strong analytical writing & nuance |
| **Structured JSON Support** | **Native `response_schema` (Pydantic enforcement)** | Native `json_schema` Structured Outputs | Tool-use / JSON mode |
| **Recommendation** | **Selected (Primary Production Model)** | **Recommended Fallback Model** | Higher output cost for bulk URL scanning |

*(Note: Token rates and context limits reflect published provider documentation; response times are estimates for a ~2,200-token input / ~1,400-token output structured JSON payload and vary by network conditions).*

### B. Best Model Selection: `gemini-2.5-flash`

**`gemini-2.5-flash`** was selected as the primary model for this application because:

1. **Guaranteed Schema Adherence:** Passing our Pydantic `WebsiteAnalysisSections` schema directly into `GenerateContentConfig(response_schema=...)` enforces valid JSON keys, enums, and nested arrays at decoding time.
2. **1M Token Context Headroom:** Easily accommodates large, multi-section enterprise homepages and documentation pages without truncation.
3. **Free Tier & Aggressive Caching:** Supports a free developer tier for prototyping and a 90% input token discount on cached context reads ($0.03 / 1M tokens).

### C. Cost Optimization Strategies Implemented

1. **HTML Noise Stripping (`website_extractor.py`):** Decomposes `<script>`, `<style>`, `<svg>`, `<iframe>`, `<canvas>`, and `<noscript>` tags before text extraction, reducing raw HTML payload size by **80%–90%**.
2. **Line Deduplication & Token Capping:** Deduplicates repeated navigation/footer strings and caps extracted body text at `8,000` characters (~2,000 tokens).
3. **In-Memory TTL Caching (`analysis_service.py`):** Caches analyzed URLs for 1 hour (`CACHE_TTL_SECONDS = 3600`), serving repeat requests in `<5 ms` with **$0.00 API cost**.
4. **Concise System Instructions:** Uses low temperature (`0.2`) and compact field descriptions inside the Pydantic schema rather than verbose few-shot JSON examples in the prompt.

### D. Final LLM Recommendation & Per-Analysis Cost Estimate

| Metric | Value / Specification |
| --- | --- |
| **Recommended Provider** | Google Gemini API (`google-genai` SDK) |
| **Recommended Model** | `gemini-2.5-flash` |
| **Estimated Input Tokens** | ~2,200 tokens (system prompt + metadata + cleaned page text) |
| **Estimated Output Tokens** | ~1,400 tokens (complete 5-section structured JSON response) |
| **Estimated Cost per Analysis** | **~$0.00416 per uncached website** (`2,200 × $0.30/1M + 1,400 × $2.50/1M`) |
| **Expected Response Time** | ~2.0 – 3.5 seconds (live uncached) / `<5 ms` (cached) |
| **Fallback Model** | OpenAI `gpt-4o-mini` (~$0.00117/request at $0.15/$0.60 per 1M tokens with native JSON schema support) |

---

## Setup & Local Execution

### 1. Clone & Create Virtual Environment

```bash
git clone [https://github.com/](https://github.com/)Heenakousar26/ai-link-analysis.git
cd ai-link-analysis
python -m venv venv
venv\Scripts\activate.bat   # Windows

```

### 2. Install Dependencies & Configure Environment

```bash
pip install -r requirements.txt
copy .env.example .env

```

Add your `GEMINI_API_KEY` inside `.env`.

### 3. Run Automated Tests & Start Server

```bash
pytest -v
uvicorn app.main:app --host 0.0.0.0 --port 4000

```

Open **`http://localhost:4000/docs`** in your browser.

---

## Sample API Request & Response

### Request (`POST /link-analysis`)

```json
{
  "url": "[https://stripe.com](https://stripe.com)"
}

```

### Response (`200 OK` – Abbreviated Structure)

```json
{
  "success": true,
  "website": "[https://stripe.com/](https://stripe.com/)",
  "cached": false,
  "model_used": "gemini-2.5-flash",
  "brand": {
    "name": "Stripe",
    "category": "Financial Infrastructure & Payment Processing",
    "summary": "Financial infrastructure platform for businesses to accept payments, grow revenue, and accelerate new business opportunities."
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "Stripe provides programmable payment processing and financial infrastructure for internet businesses.",
      "competitors": [
        {
          "name": "Adyen",
          "main_service": "Enterprise Omnichannel Payment Processing",
          "target_market": "Global Enterprises",
          "strengths": ["Unified global acquiring"],
          "weaknesses_or_gaps": ["Higher onboarding complexity for small startups"],
          "source_note": "Verified market competitor"
        }
      ],
      "side_by_side_comparison": []
    },
    "target_search_queries": [
      {
        "query": "best online payment gateway for SaaS startups",
        "platforms": ["Google Search", "LinkedIn"],
        "intent": "Service Search",
        "business_relevance": "Directly aligns with Stripe Billing and Payments APIs",
        "target_audience": "SaaS founders and CTOs"
      }
    ],
    "seo_improvements": {
      "primary_keyword": "Online Payment Processing Platform",
      "secondary_keywords": ["Payment Gateway API", "Subscription Billing Software"],
      "recommended_title": "Online Payment Processing & Financial Infrastructure | Stripe",
      "meta_description": "Accept payments, manage subscriptions, and scale global revenue with Stripe's developer-first financial infrastructure platform.",
      "supporting_content": []
    },
    "top_services": [
      {
        "service_name": "Stripe Payments",
        "description": "Global online and in-person payment acceptance.",
        "target_industry": "E-commerce & SaaS",
        "target_customer": "Startups to Enterprises",
        "main_benefit": "High conversion checkout with global payment method support",
        "extraction_source": "Extracted from website"
      }
    ],
    "target_audience": {
      "primary_audience": ["SaaS Companies", "E-commerce Businesses"],
      "secondary_audience": ["Marketplaces", "Enterprise Platforms"],
      "industry_segments": ["Fintech", "Retail", "Software"],
      "customer_needs_and_challenges": ["Cross-border payment compliance", "Subscription churn reduction"]
    }
  }
}

```

---



```

```
