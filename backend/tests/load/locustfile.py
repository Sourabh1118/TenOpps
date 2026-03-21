"""
Main Locust load testing file for Job Aggregation Platform

This file defines the primary load testing scenarios for the platform.
Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000

Validates: Requirements 16.1, 16.2, 16.3
"""

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask
import random
import json
import time
from typing import Dict, Any


class JobSeekerUser(HttpUser):
    """
    Simulates a job seeker browsing and searching for jobs
    
    Weight: 70% of total users (most common user type)
    """
    
    weight = 70
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    
    def on_start(self):
        """Initialize user session"""
        self.job_ids = []
        self.search_queries = [
            "software engineer",
            "data scientist",
            "product manager",
            "designer",
            "marketing manager",
            "sales representative",
            "accountant",
            "teacher",
            "nurse",
            "developer"
        ]
        self.locations = [
            "San Francisco",
            "New York",
            "London",
            "Berlin",
            "Tokyo",
            "Remote"
        ]
    
    @task(40)
    def search_jobs(self):
        """
        Search for jobs with various filters
        Most common action - 40% of requests
        """
        query = random.choice(self.search_queries)
        location = random.choice(self.locations)
        
        params = {
            "query": query,
            "location": location,
            "page": 1,
            "page_size": 20
        }
        
        # Randomly add additional filters
        if random.random() > 0.5:
            params["remote"] = "true"
        
        if random.random() > 0.7:
            params["job_type"] = random.choice(["FULL_TIME", "PART_TIME", "CONTRACT"])
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="/api/jobs/search"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Store job IDs for later viewing
                if "results" in data and len(data["results"]) > 0:
                    self.job_ids = [job["id"] for job in data["results"][:5]]
                    response.success()
                else:
                    response.success()
            else:
                response.failure(f"Search failed with status {response.status_code}")
    
    @task(30)
    def view_job_details(self):
        """
        View detailed job posting
        Second most common action - 30% of requests
        """
        if not self.job_ids:
            # If no jobs cached, search first
            raise RescheduleTask()
        
        job_id = random.choice(self.job_ids)
        
        with self.client.get(
            f"/api/jobs/{job_id}",
            catch_response=True,
            name="/api/jobs/[id]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Job might have expired, remove from cache
                self.job_ids.remove(job_id)
                response.failure("Job not found")
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(10)
    def browse_featured_jobs(self):
        """
        Browse featured job listings
        10% of requests
        """
        with self.client.get(
            "/api/jobs/search",
            params={"featured": "true", "page": 1, "page_size": 10},
            catch_response=True,
            name="/api/jobs/search?featured=true"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(5)
    def search_with_salary_filter(self):
        """
        Search jobs with salary filters
        5% of requests
        """
        params = {
            "query": random.choice(self.search_queries),
            "salary_min": random.choice([50000, 75000, 100000, 150000]),
            "page": 1,
            "page_size": 20
        }
        
        with self.client.get(
            "/api/jobs/search",
            params=params,
            catch_response=True,
            name="/api/jobs/search?salary_min"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class EmployerUser(HttpUser):
    """
    Simulates an employer managing job postings
    
    Weight: 20% of total users
    """
    
    weight = 20
    wait_time = between(5, 10)  # Employers take more time between actions
    
    def on_start(self):
        """Initialize employer session with authentication"""
        self.token = None
        self.employer_id = None
        self.posted_job_ids = []
        
        # Login as employer
        self.login()
    
    def login(self):
        """Authenticate as employer"""
        # In real test, use actual test credentials
        credentials = {
            "email": f"employer_{random.randint(1, 100)}@test.com",
            "password": "testpassword123"
        }
        
        with self.client.post(
            "/api/auth/login",
            json=credentials,
            catch_response=True,
            name="/api/auth/login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.employer_id = data.get("user_id")
                response.success()
            else:
                # If login fails, use mock token for testing
                self.token = "mock_token_for_testing"
                response.failure("Login failed, using mock token")
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(15)
    def post_job(self):
        """
        Post a new job
        15% of employer actions
        """
        if not self.token:
            raise RescheduleTask()
        
        job_data = {
            "title": f"Software Engineer - {random.randint(1, 1000)}",
            "company": f"Tech Company {random.randint(1, 100)}",
            "location": random.choice(["San Francisco", "New York", "Remote"]),
            "remote": random.choice([True, False]),
            "job_type": random.choice(["FULL_TIME", "PART_TIME", "CONTRACT"]),
            "experience_level": random.choice(["ENTRY", "MID", "SENIOR"]),
            "description": "We are looking for a talented software engineer to join our team. " * 10,
            "requirements": ["Bachelor's degree", "3+ years experience", "Python skills"],
            "responsibilities": ["Write code", "Review PRs", "Mentor juniors"],
            "salary_min": 80000,
            "salary_max": 150000,
            "salary_currency": "USD"
        }
        
        with self.client.post(
            "/api/jobs/direct",
            json=job_data,
            headers=self.get_headers(),
            catch_response=True,
            name="/api/jobs/direct [POST]"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.posted_job_ids.append(data.get("id"))
                response.success()
            elif response.status_code == 403:
                response.failure("Quota exceeded")
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(30)
    def view_dashboard(self):
        """
        View employer dashboard
        30% of employer actions
        """
        if not self.token:
            raise RescheduleTask()
        
        with self.client.get(
            "/api/employer/dashboard",
            headers=self.get_headers(),
            catch_response=True,
            name="/api/employer/dashboard"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(25)
    def view_my_jobs(self):
        """
        View employer's posted jobs
        25% of employer actions
        """
        if not self.token:
            raise RescheduleTask()
        
        with self.client.get(
            "/api/employer/jobs",
            headers=self.get_headers(),
            catch_response=True,
            name="/api/employer/jobs"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(20)
    def view_applications(self):
        """
        View applications for posted jobs
        20% of employer actions
        """
        if not self.token or not self.posted_job_ids:
            raise RescheduleTask()
        
        job_id = random.choice(self.posted_job_ids)
        
        with self.client.get(
            f"/api/employer/jobs/{job_id}/applications",
            headers=self.get_headers(),
            catch_response=True,
            name="/api/employer/jobs/[id]/applications"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(10)
    def import_job_from_url(self):
        """
        Import job from external URL
        10% of employer actions
        """
        if not self.token:
            raise RescheduleTask()
        
        # Mock URLs for testing
        test_urls = [
            "https://www.linkedin.com/jobs/view/123456",
            "https://www.indeed.com/viewjob?jk=abcdef123456",
            "https://www.naukri.com/job-listings-software-engineer-123456"
        ]
        
        import_data = {
            "url": random.choice(test_urls)
        }
        
        with self.client.post(
            "/api/jobs/import-url",
            json=import_data,
            headers=self.get_headers(),
            catch_response=True,
            name="/api/jobs/import-url [POST]"
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            elif response.status_code == 403:
                response.failure("Import quota exceeded")
            else:
                response.failure(f"Failed with status {response.status_code}")


class AnonymousUser(HttpUser):
    """
    Simulates anonymous users browsing without authentication
    
    Weight: 10% of total users
    """
    
    weight = 10
    wait_time = between(3, 8)
    
    @task(60)
    def browse_jobs(self):
        """Browse jobs without filters"""
        with self.client.get(
            "/api/jobs/search",
            params={"page": random.randint(1, 5), "page_size": 20},
            catch_response=True,
            name="/api/jobs/search [anonymous]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(30)
    def view_homepage(self):
        """View homepage/landing page"""
        with self.client.get(
            "/",
            catch_response=True,
            name="/ [homepage]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(10)
    def check_health(self):
        """Check API health endpoint"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


# Event handlers for custom metrics and logging

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("=" * 60)
    print("Load Test Starting")
    print(f"Target host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("=" * 60)
    print("Load Test Completed")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")
    print("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Called for every request
    Can be used for custom metrics or logging
    """
    # Log slow requests
    if response_time > 1000:  # More than 1 second
        print(f"SLOW REQUEST: {name} took {response_time:.2f}ms")
    
    # Log errors
    if exception:
        print(f"ERROR: {name} failed with {exception}")
