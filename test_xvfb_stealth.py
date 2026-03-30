import asyncio
import os
import sys
import time
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# Add app directory to path
sys.path.append('/home/jobplatform/job-platform/backend')

async def test_platform(name, url, search_selector):
    print(f"\n--- Testing {name} Stealth ---")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    print(f"Initializing UC driver (headless=False, xvfb={os.environ.get('DISPLAY')})...")
    
    try:
        # Force version 146 to match installed Chrome
        driver = uc.Chrome(options=options, headless=False, version_main=146)
        driver.set_window_size(random.randint(1280, 1600), random.randint(720, 1000))
        
        print(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for content or block
        time.sleep(15)
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Check for blocks
        if "Cloudflare" in page_source and ("429" in page_source or "Access denied" in page_source):
            print(f"FAIL: {name} BLOCKED by Cloudflare (429/Access Denied)")
        elif "captcha-delivery.com" in page_source or "captcha" in page_source.lower():
            print(f"FAIL: {name} BLOCKED by DataDome CAPTCHA")
        elif soup.select(search_selector):
            print(f"SUCCESS: Found job cards for {name}!")
        else:
            print(f"WARNING: No specific block detected, but also no job cards found.")
            # Save debug HTML for analysis
            debug_path = f"/home/jobplatform/job-platform/backend/logs/{name}_diagnostic.html"
            with open(debug_path, "w") as f:
                f.write(page_source)
            print(f"Diagnostic HTML saved to {debug_path}")
        
        driver.quit()
    except Exception as e:
        print(f"ERROR testing {name}: {e}")

async def main():
    await test_platform("Indeed", "https://www.indeed.com/jobs?q=software+engineer&l=New+York", "div.job_seen_beacon")
    await test_platform("Monster", "https://www.monster.com/jobs/search?q=software-engineer", "div[class*='job-card']")

if __name__ == "__main__":
    asyncio.run(main())
