import os
import sys
from dotenv import load_dotenv
import undetected_chromedriver as uc
import time

# Load environment variables
load_dotenv()

def verify():
    token = os.getenv("SCRAPE_DO_TOKEN")
    if not token:
        print("ERROR: SCRAPE_DO_TOKEN not found in .env file.")
        return

    print(f"Testing Indeed with Scrape.do SUPER + RENDER proxy...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Using Super Proxy (residential) + Render (JS) via Scrape.do Proxy Endpoint
    # Format: token-super-render
    proxy_url = f"http://{token}-super-render@proxy.scrape.do:8080"
    options.add_argument(f'--proxy-server={proxy_url}')
    
    headless = not os.environ.get('DISPLAY')
    
    try:
        driver = uc.Chrome(options=options, headless=headless, version_main=146)
        print("Navigating to Indeed Search...")
        driver.get("https://www.indeed.com/jobs?q=software+engineer&l=New+York")
        time.sleep(20)
        
        print(f"Page Title: {driver.title}")
        with open("/tmp/indeed_scrape_do_debug.html", "w") as f:
            f.write(driver.page_source)
        
        if "Indeed" in driver.title and "software engineer" in driver.page_source.lower():
            print("SUCCESS: Indeed search results loaded with Scrape.do!")
        else:
            print(f"RESULT: Blocked or Unexpected state. Title: {driver.title}")
            print(f"Debug HTML saved to /tmp/indeed_scrape_do_debug.html")
            
        driver.quit()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verify()
