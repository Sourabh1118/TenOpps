import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Simulation of the BaseScraper setup
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def test_chrome():
    print("Testing Chrome initialization...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    os.environ['SE_CACHE_PATH'] = '/tmp/selenium-manager-cache'
    
    log_path = os.path.join(os.getcwd(), "logs", "test_chromedriver.log")
    print(f"Logging to: {log_path}")
    
    service = Service(
        log_output=log_path,
        service_args=["--verbose"]
    )
    
    try:
        driver = webdriver.Chrome(options=chrome_options, service=service)
        print("SUCCESS: Chrome initialized!")
        driver.get("https://www.google.com")
        print(f"Page title: {driver.title}")
        driver.quit()
        print("SUCCESS: Chrome closed!")
    except Exception as e:
        print(f"FAILURE: {e}")
        if os.path.exists(log_path):
            print("\n--- CHROMEDRIVER LOG SNIPPET ---")
            with open(log_path, 'r') as f:
                print(f.read()[-1000:]) # Last 1000 chars

if __name__ == "__main__":
    test_chrome()
