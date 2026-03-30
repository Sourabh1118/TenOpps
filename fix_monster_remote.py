import re

path = '/home/jobplatform/job-platform/backend/app/services/scraping.py'
with open(path, 'r') as f:
    content = f.read()

new_monster_class = r"""class MonsterScraper(BaseScraper):
    \"\"\"
    Monster web scraper using Selenium in Stealth mode.
    
    Implements Requirements 1.4, 1.5:
    - Fetches jobs from Monster.com via search results
    - Navigates to individual job pages via Selenium to bypass DataDome
    - Extracts full job details including LD+JSON schema
    - Normalizes Monster data to standard schema
    \"\"\"
    
    def __init__(self, search_url: str, rate_limit: int = 5):
        super().__init__(source_name="monster", rate_limit=rate_limit)
        self.search_url = search_url
        self.base_url = "https://www.monster.com"
        logger.info(f"Initialized Monster scraper for URL: {search_url}")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        \"\"\"Scrape jobs from Monster search results.\"\"\"
        try:
            logger.info(f"Fetching Monster search results (Stealth): {self.search_url}")
            
            self.driver = self._init_driver(stealth=True)
            if not self.driver:
                raise ScrapingError("Failed to initialize Stealth Selenium driver for Monster")
                
            self.driver.get(self.search_url)
            
            # Step 1: Wait for job cards
            try:
                wait = WebDriverWait(self.driver, 20)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='job-card'], [data-testid='job-card']")))
                time.sleep(2)
            except TimeoutException:
                logger.warning("Timed out waiting for Monster job cards")
                self._save_debug_html(self.driver.page_source, f"monster_search_timeout_{int(time.time())}")
                return []
            
            # Step 2: Extract URLs
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            job_urls = self._extract_job_urls(soup)
            
            if not job_urls:
                logger.warning("No job URLs found in Monster search results")
                return []
            
            logger.info(f"Found {len(job_urls)} job URLs on Monster")
            
            # Step 3: Fetch details for each URL (limit 15)
            jobs = []
            for job_url in job_urls[:15]:
                try:
                    await self.wait_for_rate_limit()
                    time.sleep(random.uniform(4.0, 8.0))
                    
                    logger.debug(f"Fetching Monster detail: {job_url}")
                    self.driver.get(job_url)
                    
                    try:
                        wait = WebDriverWait(self.driver, 15)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='job-description'], #JobDescription, h1[class*='title']")))
                    except TimeoutException:
                        logger.warning(f"Timeout waiting for Monster details: {job_url}")
                        continue
                    
                    # Parse job page HTML
                    job_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    job_data = self._parse_job_page(job_soup, job_url)
                    
                    if job_data and self._validate_job_data(job_data):
                        jobs.append(job_data)
                        logger.info(f"Successfully scraped Monster job: {job_data['title']}")
                except Exception as e:
                    logger.error(f"Error parsing Monster detail {job_url}: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Monster scrape failure: {e}")
            raise ScrapingError(str(e))
        finally:
            self._close_driver()

    def _extract_job_urls(self, soup: BeautifulSoup) -> List[str]:
        \"\"\"Extract job URLs from Monster search results.\"\"\"
        job_urls = []
        # Modern Monster selectors (Partial match for dynamic classes)
        anchors = soup.select('a[class*=\"job-name\"]') or \
                  soup.select('a[class*=\"title\"]') or \
                  soup.select('h2 a') or \
                  soup.select('a[data-testid=\"job-card-link\"]')
        
        for a in anchors:
            url = a.get('href', '')
            if url:
                if not url.startswith('http'):
                    url = self.base_url + url
                if url not in job_urls:
                    job_urls.append(url)
        return job_urls

    def _parse_job_page(self, soup: BeautifulSoup, job_url: str) -> Optional[Dict[str, Any]]:
        \"\"\"Parse Monster job detail page using LD+JSON and DOM fallback.\"\"\"
        try:
            # LD+JSON Strategy
            import json
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    ld_list = data if isinstance(data, list) else [data]
                    for ld in ld_list:
                        if ld.get('@type') == 'JobPosting':
                            return {
                                'title': ld.get('title', 'Untitled Position'),
                                'company': ld.get('hiringOrganization', {}).get('name', 'Unknown Company'),
                                'location': ld.get('jobLocation', {}).get('address', {}).get('addressLocality', 'Remote'),
                                'description': BeautifulSoup(ld.get('description', ''), 'html.parser').get_text(separator='\\n', strip=True),
                                'url': job_url,
                                'posted': ld.get('datePosted', ''),
                                'job_type': ld.get('employmentType', 'Full-Time'),
                                'salary': str(ld.get('baseSalary', {}).get('value', {}).get('value', '')),
                                'requirements': '',
                            }
                except:
                    continue

            # Fallback to DOM parsing
            title_elem = soup.select_one('h1[class*=\"job-name\"]') or \
                         soup.select_one('h1[class*=\"title\"]') or \
                         soup.select_one('h1')
            title = title_elem.get_text(strip=True) if title_elem else 'Untitled Position'
            
            company_elem = soup.select_one('h2[class*=\"company-name\"]') or \
                           soup.select_one('div[class*=\"company\"]') or \
                           soup.select_one('a[class*=\"company\"]')
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
            
            desc_elem = soup.select_one('div[class*=\"job-description\"]') or \
                        soup.select_one('#JobDescription') or \
                        soup.select_one('div[class*=\"description\"]')
            description = desc_elem.get_text(separator='\\n', strip=True) if desc_elem else ''
            
            location_elem = soup.select_one('[class*=\"location\"]') or \
                            soup.select_one('[itemprop=\"jobLocation\"]')
            location = location_elem.get_text(strip=True) if location_elem else 'Not specified'
            
            job_type_elem = soup.select_one('[class*=\"job-type\"]') or \
                            soup.select_one('[class*=\"employment-type\"]')
            job_type = job_type_elem.get_text(strip=True) if job_type_elem else 'Full-Time'
            
            requirements_elem = soup.select_one('[class*=\"requirements\"]') or \
                                soup.select_one('[class*=\"qualifications\"]')
            requirements = requirements_elem.get_text(strip=True) if requirements_elem else ''
            
            posted_elem = soup.select_one('[class*=\"posted-date\"]') or \
                          soup.select_one('time[class*=\"posted\"]')
            posted = posted_elem.get_text(strip=True) if posted_elem else ''
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': job_url,
                'posted': posted,
                'job_type': job_type,
                'salary': '',
                'requirements': requirements,
            }
        except Exception as e:
            logger.error(f"Monster detail parse error: {e}")
            return None
"""

pattern = re.compile(r'class MonsterScraper\(BaseScraper\):.*?    def normalize_job', re.DOTALL)
replacement = new_monster_class + "\n\n    def normalize_job"

new_content = pattern.sub(replacement, content)

with open(path, 'w') as f:
    f.write(new_content)
