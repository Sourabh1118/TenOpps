import undetected_chromedriver as uc
import time
import random
import os

def test():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Check for Xvfb display
    headless = not os.environ.get('DISPLAY')
    print(f"Initializing UC driver (headless={headless}, DISPLAY={os.environ.get('DISPLAY')})...")
    
    driver = uc.Chrome(options=options, headless=headless, version_main=146)
    driver.set_window_size(1400, 900)
    
    try:
        # Step 1: Prime with Google
        print("Step 1: Priming with Google...")
        driver.get("https://www.google.com")
        time.sleep(random.uniform(3, 5))
        
        # Step 2: Monster Priming
        print("Step 2: Visiting Monster Home...")
        driver.get("https://www.monster.com")
        time.sleep(random.uniform(5, 8))
        print(f"Monster Home Title: {driver.title}")
        
        if "captcha" not in driver.page_source.lower():
            print("Monster Home OK, searching...")
            driver.get("https://www.monster.com/jobs/search?q=software-engineer")
            time.sleep(15)
            print(f"Monster Search Title: {driver.title}")
            print(f"Monster Blocked?: {'captcha-delivery.com' in driver.page_source}")
        else:
            print("Monster Home BLOCKED by DataDome")
            
        print("---")
        
        # Step 3: Indeed Priming
        print("Step 3: Visiting Indeed Home...")
        driver.get("https://www.indeed.com")
        time.sleep(random.uniform(5, 8))
        print(f"Indeed Home Title: {driver.title}")
        
        if "moment" not in driver.title.lower():
            print("Indeed Home OK, searching...")
            driver.get("https://www.indeed.com/jobs?q=software+engineer&l=New+York")
            time.sleep(15)
            print(f"Indeed Search Title: {driver.title}")
            print(f"Indeed Blocked?: {'429' in driver.page_source or 'moment' in driver.title.lower()}")
        else:
            print("Indeed Home BLOCKED by Cloudflare")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    test()
