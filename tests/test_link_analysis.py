from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app, analysis_service
from app.schemas import (
    AudienceSegment,
    BrandSummary,
    CompetitorAnalysis,
    CompetitorDetail,
    SEOImprovements,
    ServiceItem,
    SupportingContentIdea,
    TargetAudience,
    TargetSearchQuery,
    WebsiteAnalysisSections,
)
from app.services.website_extractor import WebsiteExtractor

client = TestClient(app)


def test_ssrf_blocks_localhost_and_private_ips():
    for blocked_url in [
        "http://localhost:4000",
        "http://127.0.0.1:8080",
        "http://169.254.169.254/latest/meta-data/",
        "http://192.168.1.1",
    ]:
        response = client.post("/link-analysis", json={"url": blocked_url})
        assert response.status_code == 422


def test_html_extractor_strips_scripts_and_extracts_metadata():
    sample_html = """
    <html>
      <head>
        <title>Acme Cloud - Scalable Web Hosting</title>
        <meta name="description" content="Fast cloud hosting for startups and SMBs.">
        <script>console.log("tracking noise");</script>
        <style>.hidden { display: none; }</style>
      </head>
      <body>
        <h1>Managed Cloud Hosting</h1>
        <h2>Built for Modern Developers</h2>
        <p>Deploy applications in seconds with automated backups and 99.99% uptime.</p>
      </body>
    </html>
    """
    extractor = WebsiteExtractor()
    parsed = extractor._parse_html("https://acmecloud.example.com", sample_html)
    assert parsed["title"] == "Acme Cloud - Scalable Web Hosting"
    assert parsed["meta_description"] == "Fast cloud hosting for startups and SMBs."
    assert "Managed Cloud Hosting" in parsed["headings"]
    assert "tracking noise" not in parsed["body_text"]
    assert "Deploy applications in seconds" in parsed["body_text"]


def test_link_analysis_endpoint_returns_all_five_sections():
    mock_sections = WebsiteAnalysisSections(
        brand=BrandSummary(
            name="Acme Cloud",
            category="Cloud Infrastructure",
            summary="Managed cloud hosting platform for startups and SMBs.",
        ),
        competitor_analysis=CompetitorAnalysis(
            brand_overview="Acme Cloud provides simplified managed cloud hosting.",
            main_products_and_services=["Managed Cloud Hosting", "Automated Backups"],
            competitors=[
                CompetitorDetail(
                    name="DigitalOcean",
                    main_service="Cloud Virtual Machines",
                    target_market="Developers & Startups",
                    strengths=["Simple UI", "Predictable pricing"],
                    weaknesses_or_gaps=["Less hands-on managed support"],
                    source_note="Verified market competitor",
                ),
                CompetitorDetail(
                    name="Render",
                    main_service="Managed PaaS Hosting",
                    target_market="Web Developers",
                    strengths=["Git-push deployments"],
                    weaknesses_or_gaps=["Higher cost at scale"],
                    source_note="Verified market competitor",
                ),
                CompetitorDetail(
                    name="Linode (Akamai)",
                    main_service="Linux Cloud Instances",
                    target_market="SMBs & Enterprises",
                    strengths=["Global edge network"],
                    weaknesses_or_gaps=["Steeper learning curve"],
                    source_note="Verified market competitor",
                ),
            ],
            brand_competitive_advantages=["Zero-config automated backups"],
            opportunities=["Target non-technical founders with one-click templates"],
        ),
        target_search_queries=[
            TargetSearchQuery(
                query="best managed cloud hosting for startups",
                platforms=["Google Search", "LinkedIn"],
                intent="Service Search",
                business_relevance="Directly matches core managed hosting offering",
                target_audience="Startup CTOs and founders",
            ),
            TargetSearchQuery(
                query="affordable web app hosting with automated backups",
                platforms=["Google Search", "X (Twitter)"],
                intent="Service Discovery",
                business_relevance="Highlights key differentiator",
                target_audience="Indie developers and SMBs",
            ),
            TargetSearchQuery(
                query="cloud hosting setup tips for small business",
                platforms=["Facebook", "Instagram"],
                intent="Inspiration",
                business_relevance="Top-of-funnel educational discovery",
                target_audience="Small business owners",
            ),
            TargetSearchQuery(
                query="managed cloud infrastructure provider for SaaS",
                platforms=["LinkedIn"],
                intent="B2B Search",
                business_relevance="Matches B2B SaaS deployment needs",
                target_audience="B2B SaaS engineering leads",
            ),
            TargetSearchQuery(
                query="fast cloud deployment alternative to AWS",
                platforms=["Google Search", "X (Twitter)"],
                intent="Service Search",
                business_relevance="Captures users seeking simpler alternatives",
                target_audience="Full-stack developers",
            ),
        ],
        seo_improvements=SEOImprovements(
            primary_keyword="Managed Cloud Hosting",
            secondary_keywords=["Cloud Hosting for Startups", "Automated Cloud Backups"],
            long_tail_keywords=["best managed cloud hosting for small business"],
            relevant_business_keywords=["PaaS", "Cloud Deployment", "Web Hosting"],
            recommended_title="Managed Cloud Hosting for Startups & SMBs | Acme Cloud",
            title_improvement_notes="Places primary keyword first and defines target audience clearly.",
            meta_description="Deploy scalable apps in seconds with Acme Cloud. Fast managed cloud hosting, automated backups, and 99.99% uptime for growing startups.",
            supporting_content=[
                SupportingContentIdea(
                    content_type="Service Landing Page",
                    title_or_topic="Managed Cloud Hosting for SaaS Startups",
                    purpose="Captures high-intent B2B SaaS buyers",
                )
            ],
        ),
        top_services=[
            ServiceItem(
                service_name="Managed Cloud Hosting",
                description="High-availability cloud server hosting.",
                target_industry="Technology & SaaS",
                target_customer="Startups and SMBs",
                main_benefit="Eliminates server maintenance overhead",
                extraction_source="Extracted from website",
            )
        ],
        target_audience=TargetAudience(
            primary_audience=["SaaS Startups", "Small and Medium Businesses"],
            secondary_audience=["Freelance Web Developers", "Digital Agencies"],
            industry_segments=["Software", "E-commerce", "Digital Media"],
            business_types=["B2B Startups", "SMBs"],
            customer_profiles=["CTOs", "Lead Full-Stack Developers", "Technical Founders"],
            geographical_focus="Global",
            customer_needs_and_challenges=["Complex DevOps setup", "Downtime risks"],
            customer_interests=["Fast deployment", "Automated backups", "Predictable cloud billing"],
            recommended_marketing_segments=[
                AudienceSegment(
                    segment_name="Early-Stage SaaS Startups",
                    business_type="B2B Technology",
                    key_requirement="Zero-DevOps cloud deployment",
                )
            ],
        ),
    )

    orig_extract = analysis_service.extractor.extract
    orig_analyze = analysis_service.llm_service.analyze_website

    analysis_service.extractor.extract = AsyncMock(
        return_value={"final_url": "https://example.com", "title": "Acme Cloud"}
    )
    analysis_service.llm_service.analyze_website = AsyncMock(return_value=mock_sections)

    try:
        response = client.post("/link-analysis", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["brand"]["name"] == "Acme Cloud"
        assert "competitor_analysis" in data["analysis"]
        assert "target_search_queries" in data["analysis"]
        assert "seo_improvements" in data["analysis"]
        assert "top_services" in data["analysis"]
        assert "target_audience" in data["analysis"]
    finally:
        analysis_service.extractor.extract = orig_extract
        analysis_service.llm_service.analyze_website = orig_analyze