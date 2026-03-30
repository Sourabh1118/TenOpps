import undetected_chromedriver as uc
import time
import random
import os
import sys

def test():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # MOBILE USER AGENT
    mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    options.add_argument(f"user-agent={mobile_ua}")
    
    headless = not os.environ.get('DISPLAY')
    print(f"Initializing UC Mobile Driver (headless={headless})...")
    sys.stdout.flush()
    
    try:
        driver = uc.Chrome(options=options, headless=headless, version_main=146)
        driver.set_window_size(390, 844) 
        
        print("Step 1: Priming from Google Search...")
        sys.stdout.flush()
        driver.get("https://www.google.com/search?q=indeed+jobs+new+york")
        time.sleep(5)
        
        print("Step 2: Checking Indeed Mobile...")
        sys.stdout.flush()
        driver.get("https://www.indeed.com/m/jobs?q=software+engineer&l=New+York")
        time.sleep(15)
        print(f"Indeed Title: {driver.title}")
        with open("/tmp/indeed_mobile_debug.html", "w") as f:
            f.write(driver.page_source)
        
        print("Step 3: Checking Monster Mobile...")
        sys.stdout.flush()
        driver.get("https://www.monster.com/jobs/search?q=software-engineer")
        time.sleep(15)
        print(f"Monster Title: {driver.title}")
        with open("/tmp/monster_mobile_debug.html", "w") as f:
            f.write(driver.page_source)
            
        driver.quit()
        print("Test Complete.")
    except Exception as e:
        print(f"ERROR: {e}")
    sys.stdout.flush()

if __name__ == "__main__":
    test()
