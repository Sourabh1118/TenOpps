"""
Search Performance Load Testing

Tests search functionality with large datasets and various query patterns.
Validates: Requirement 16.2 - Search performance with large dataset

Run with: locust -f tests/load/test_search_performance.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import random
import time


class SearchPerformanceUser(HttpUser):
    """
    User focused on testing search performance with various query patterns
    """
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize search test data"""
        self.simple_queries = [
            "engineer",
            "developer",
            "manager",
            "designer",
            "analyst",
            "consultant",
            "specialist",
            "coordinator",
            "director",
            "lead"
        ]
        
        self.complex_queries = [
            "senior software engineer python",
            "full stack developer react node",
            "data scientist machine learning",
            "product manager saas b2b",
            "ux designer mobile apps",
            "devops engineer kubernetes aws",
            "backend developer java spring",
            "frontend developer vue typescript",
            "security engineer penetration testing",
            "cloud architect azure solutions"
        ]
        
        self.locations = [
            "San Francisco, CA",
            "New York, NY",
            "London, UK",
            "Berlin, Germany",
            "Tokyo, Japan",
            "Toronto, Canada",
            "Sydney, Australia",
            "Singapore",
            "Remote",
            "Hybrid"
        ]
        
        self.job_types = ["FULL_TIME", "PART_TIME", "CONTRACT", "FREELANCE", "INTERNSHIP"]
        self.experience_levels = ["ENTRY", "MID", "SENIOR", "LEAD", "EXECUTIVE"]
    
    @task(50)
    def simple_keyword_search(self):
        """
        Simple keyword search - most common pattern
        50% of search requests
        """
        query = random.choice(self.simple_queries)
        
        params = {
            "query": query,
            "page": 1,
            "page_size": 20
        }
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="Search: Simple Keyword"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Verify response structure
                if "results" in data and "total" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(30)
    def multi_filter_search(self):
        """
        Search with multiple filters
        30% of search requests
        """
        query = random.choice(self.complex_queries)
        location = random.choice(self.locations)
        
        params = {
            "query": query,
            "location": location,
            "job_type": random.choice(self.job_types),
            "experience_level": random.choice(self.experience_levels),
            "page": 1,
            "page_size": 20
        }
        
        # Add salary filter 50% of the time
        if random.random() > 0.5:
            params["salary_min"] = random.choice([50000, 75000, 100000, 150000])
        
        # Add remote filter 30% of the time
        if random.random() > 0.7:
            params["remote"] = "true"
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="Search: Multi-Filter"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(20)
    def location_based_search(self):
        """
        Location-focused search
        20% of search requests
        """
        location = random.choice(self.locations)
        
        params = {
            "location": location,
            "page": 1,
            "page_size": 20
        }
        
        # Add remote filter for some searches
        if "Remote" not in location and random.random() > 0.5:
            params["remote"] = "true"
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="Search: Location-Based"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(15)
    def paginated_search(self):
        """
        Test pagination performance
        15% of search requests
        """
        query = random.choice(self.simple_queries)
        page = random.randint(1, 10)  # Test various page numbers
        
        params = {
            "query": query,
            "page": page,
            "page_size": random.choice([10, 20, 50, 100])
        }
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name=f"Search: Pagination (page {page})"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Verify pagination metadata
                if "page" in data and "total_pages" in data:
                    response.success()
                else:
                    response.failure("Missing pagination metadata")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(10)
    def salary_range_search(self):
        """
        Search with salary range filters
        10% of search requests
        """
        salary_ranges = [
            (50000, 80000),
            (80000, 120000),
            (120000, 180000),
            (180000, 250000)
        ]
        
        salary_min, salary_max = random.choice(salary_ranges)
        
        params = {
            "query": random.choice(self.simple_queries),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "page": 1,
            "page_size": 20
        }
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="Search: Salary Range"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(5)
    def recent_jobs_search(self):
        """
        Search for recently posted jobs
        5% of search requests
        """
        params = {
            "posted_within": random.choice([1, 3, 7, 14, 30]),  # days
            "page": 1,
            "page_size": 20
        }
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="Search: Recent Jobs"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(5)
    def featured_jobs_search(self):
        """
        Search for featured jobs only
        5% of search requests
        """
        params = {
            "featured": "true",
            "page": 1,
            "page_size": 20
        }
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="Search: Featured Jobs"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(5)
    def source_type_search(self):
        """
        Search by source type
        5% of search requests
        """
        source_types = ["direct", "url_import", "aggregated"]
        
        params = {
            "source_type": random.choice(source_types),
            "page": 1,
            "page_size": 20
        }
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="Search: By Source Type"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


# Custom metrics tracking

search_response_times = []
cache_hits = 0
cache_misses = 0


@events.request.add_listener
def track_search_metrics(request_type, name, response_time, response_length, exception, **kwargs):
    """Track search-specific metrics"""
    global search_response_times, cache_hits, cache_misses
    
    if "Search:" in name and not exception:
        search_response_times.append(response_time)
        
        # Track cache performance (would need to check response headers in real implementation)
        # For now, assume fast responses are cache hits
        if response_time < 100:
            cache_hits += 1
        else:
            cache_misses += 1


@events.test_stop.add_listener
def print_search_metrics(environment, **kwargs):
    """Print search performance metrics at end of test"""
    global search_response_times, cache_hits, cache_misses
    
    if search_response_times:
        avg_time = sum(search_response_times) / len(search_response_times)
        sorted_times = sorted(search_response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print("\n" + "=" * 60)
        print("SEARCH PERFORMANCE METRICS")
        print("=" * 60)
        print(f"Total searches: {len(search_response_times)}")
        print(f"Average response time: {avg_time:.2f}ms")
        print(f"50th percentile: {p50:.2f}ms")
        print(f"95th percentile: {p95:.2f}ms")
        print(f"99th percentile: {p99:.2f}ms")
        
        total_requests = cache_hits + cache_misses
        if total_requests > 0:
            cache_hit_rate = (cache_hits / total_requests) * 100
            print(f"\nEstimated cache hit rate: {cache_hit_rate:.1f}%")
            print(f"Cache hits: {cache_hits}")
            print(f"Cache misses: {cache_misses}")
        
        # Check against targets
        print("\n" + "-" * 60)
        print("TARGET VALIDATION")
        print("-" * 60)
        
        targets_met = True
        
        if avg_time <= 200:
            print("✓ Average response time target met (< 200ms)")
        else:
            print(f"✗ Average response time target FAILED ({avg_time:.2f}ms > 200ms)")
            targets_met = False
        
        if p95 <= 500:
            print("✓ 95th percentile target met (< 500ms)")
        else:
            print(f"✗ 95th percentile target FAILED ({p95:.2f}ms > 500ms)")
            targets_met = False
        
        if p99 <= 1000:
            print("✓ 99th percentile target met (< 1000ms)")
        else:
            print(f"✗ 99th percentile target FAILED ({p99:.2f}ms > 1000ms)")
            targets_met = False
        
        if targets_met:
            print("\n✓ ALL PERFORMANCE TARGETS MET!")
        else:
            print("\n✗ SOME PERFORMANCE TARGETS NOT MET")
        
        print("=" * 60 + "\n")
