"""
Manual test script for search API endpoint.

This script tests the search API endpoint to verify all functionality works correctly.
Run this after starting the FastAPI server.

Usage:
    python test_search_api_manual.py
"""
import requests
import json
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8000/api"


def test_search_no_filters():
    """Test search with no filters."""
    print("\n=== Test: Search with no filters ===")
    response = requests.get(f"{BASE_URL}/jobs/search")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs: {data['total']}")
        print(f"Page: {data['page']}, Page size: {data['pageSize']}")
        print(f"Total pages: {data['totalPages']}")
        print(f"Jobs returned: {len(data['jobs'])}")
        
        if data['jobs']:
            print(f"\nFirst job:")
            job = data['jobs'][0]
            print(f"  Title: {job['title']}")
            print(f"  Company: {job['company']}")
            print(f"  Location: {job['location']}")
            print(f"  Featured: {job['featured']}")
            print(f"  Quality Score: {job['qualityScore']}")
    else:
        print(f"Error: {response.text}")


def test_search_with_query():
    """Test full-text search."""
    print("\n=== Test: Full-text search ===")
    response = requests.get(f"{BASE_URL}/jobs/search", params={"query": "engineer"})
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs matching 'engineer': {data['total']}")
        
        if data['jobs']:
            print(f"\nMatching jobs:")
            for job in data['jobs'][:3]:
                print(f"  - {job['title']} at {job['company']}")
    else:
        print(f"Error: {response.text}")


def test_search_with_filters():
    """Test search with multiple filters."""
    print("\n=== Test: Search with multiple filters ===")
    params = {
        "location": "San Francisco",
        "remote": True,
        "jobType": ["FULL_TIME"],
        "page": 1,
        "page_size": 10
    }
    response = requests.get(f"{BASE_URL}/jobs/search", params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs: {data['total']}")
        print(f"Filters: San Francisco, Remote, Full-time")
        
        if data['jobs']:
            print(f"\nMatching jobs:")
            for job in data['jobs']:
                print(f"  - {job['title']} at {job['company']}")
                print(f"    Location: {job['location']}, Remote: {job['remote']}, Type: {job['jobType']}")
    else:
        print(f"Error: {response.text}")


def test_search_pagination():
    """Test pagination."""
    print("\n=== Test: Pagination ===")
    
    # First page
    response1 = requests.get(f"{BASE_URL}/jobs/search", params={"page": 1, "page_size": 2})
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"Page 1: {len(data1['jobs'])} jobs")
        print(f"Total: {data1['total']}, Total pages: {data1['totalPages']}")
        
        # Second page
        response2 = requests.get(f"{BASE_URL}/jobs/search", params={"page": 2, "page_size": 2})
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Page 2: {len(data2['jobs'])} jobs")
            
            # Verify different jobs on different pages
            if data1['jobs'] and data2['jobs']:
                job1_ids = {job['id'] for job in data1['jobs']}
                job2_ids = {job['id'] for job in data2['jobs']}
                print(f"Jobs are different: {job1_ids.isdisjoint(job2_ids)}")
    else:
        print(f"Error: {response1.text}")


def test_search_salary_filter():
    """Test salary range filter."""
    print("\n=== Test: Salary range filter ===")
    params = {
        "salaryMin": 80000,
        "salaryMax": 150000
    }
    response = requests.get(f"{BASE_URL}/jobs/search", params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs with salary $80k-$150k: {data['total']}")
        
        if data['jobs']:
            print(f"\nJobs with salary info:")
            for job in data['jobs']:
                if job['salaryMin'] or job['salaryMax']:
                    salary_range = f"${job['salaryMin']:,}" if job['salaryMin'] else "N/A"
                    salary_range += f" - ${job['salaryMax']:,}" if job['salaryMax'] else ""
                    print(f"  - {job['title']}: {salary_range}")
    else:
        print(f"Error: {response.text}")


def test_search_posted_within():
    """Test posted within filter."""
    print("\n=== Test: Posted within filter ===")
    response = requests.get(f"{BASE_URL}/jobs/search", params={"postedWithin": 7})
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs posted within 7 days: {data['total']}")
        
        if data['jobs']:
            print(f"\nRecent jobs:")
            for job in data['jobs'][:3]:
                posted_date = datetime.fromisoformat(job['postedAt'].replace('Z', '+00:00'))
                days_ago = (datetime.now(posted_date.tzinfo) - posted_date).days
                print(f"  - {job['title']} (posted {days_ago} days ago)")
    else:
        print(f"Error: {response.text}")


def test_featured_jobs_first():
    """Test that featured jobs appear first."""
    print("\n=== Test: Featured jobs appear first ===")
    response = requests.get(f"{BASE_URL}/jobs/search")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if data['jobs']:
            featured_jobs = [job for job in data['jobs'] if job['featured']]
            non_featured_jobs = [job for job in data['jobs'] if not job['featured']]
            
            print(f"Featured jobs: {len(featured_jobs)}")
            print(f"Non-featured jobs: {len(non_featured_jobs)}")
            
            if featured_jobs:
                print(f"\nFirst job is featured: {data['jobs'][0]['featured']}")
                print(f"Featured job: {data['jobs'][0]['title']}")
    else:
        print(f"Error: {response.text}")


def test_invalid_pagination():
    """Test invalid pagination parameters."""
    print("\n=== Test: Invalid pagination ===")
    
    # Page size > 100
    response = requests.get(f"{BASE_URL}/jobs/search", params={"page_size": 101})
    print(f"Page size 101 - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"  Error (expected): {response.json()}")
    
    # Page < 1
    response = requests.get(f"{BASE_URL}/jobs/search", params={"page": 0})
    print(f"Page 0 - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"  Error (expected): {response.json()}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Search API Manual Tests")
    print("=" * 60)
    print("\nMake sure the FastAPI server is running on http://localhost:8000")
    print("And that the database has some sample jobs.")
    
    try:
        test_search_no_filters()
        test_search_with_query()
        test_search_with_filters()
        test_search_pagination()
        test_search_salary_filter()
        test_search_posted_within()
        test_featured_jobs_first()
        test_invalid_pagination()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
