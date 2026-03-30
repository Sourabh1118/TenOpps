
import asyncio
import os
import sys
from typing import Optional, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Set dummy environment variables to satisfy Pydantic validation
os.environ["SECRET_KEY"] = "mock_secret_key"
os.environ["DATABASE_URL"] = "sqlite:///./mock.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"
os.environ["JWT_SECRET_KEY"] = "mock_jwt_secret"
os.environ["SCRAPE_DO_TOKEN"] = os.environ.get("SCRAPE_DO_TOKEN", "mock_token")

# Now we can import the scraper
try:
    from app.services.scraping import LinkedInScraper, ScrapingProvider
    from app.core.config import settings
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def test_linkedin_detail():
    url = "https://www.linkedin.com/jobs/view/hr-business-partner-at-jobgether-4395020069"
    print(f"Testing LinkedIn detail scraping for: {url}")
    
    # Initialize scraper
    # We use SCRAPE_DO as the provider as it's the most reliable for LinkedIn
    scraper = LinkedInScraper(rss_feed_url="", provider=ScrapingProvider.SCRAPE_DO)
    
    # Manually call the new _parse_job_page method
    description = await scraper._parse_job_page(url)
    
    if description:
        print("\nSUCCESS! Extracted description:")
        print("-" * 50)
        # Print first 500 chars
        print(description[:500] + "...")
        print("-" * 50)
        print(f"Total length: {len(description)} characters")
    else:
        print("\nFAILED: No description extracted.")

if __name__ == "__main__":
    if not settings.SCRAPE_DO_TOKEN:
        print("WARNING: SCRAPE_DO_TOKEN not set in environment or settings.")
    
    asyncio.run(test_linkedin_detail())
