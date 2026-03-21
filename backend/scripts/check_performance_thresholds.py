#!/usr/bin/env python3
"""
Performance Threshold Checker

Analyzes Locust CSV results and checks against performance thresholds.
Usage: python scripts/check_performance_thresholds.py reports/load_test_results_stats.csv
"""

import sys
import csv
from typing import List, Dict, Tuple


class PerformanceThresholds:
    """Performance thresholds for different endpoint types"""
    
    # Response time thresholds (in milliseconds)
    GET_SIMPLE_AVG = 100
    GET_SIMPLE_P95 = 200
    GET_COMPLEX_AVG = 200
    GET_COMPLEX_P95 = 500
    POST_AVG = 300
    POST_P95 = 800
    
    # Error rate threshold (percentage)
    ERROR_RATE = 1.0
    
    # RPS thresholds
    MIN_RPS = 10


def load_results(csv_path: str) -> List[Dict]:
    """
    Load Locust results from CSV file
    
    Args:
        csv_path: Path to Locust stats CSV file
    
    Returns:
        List of result dictionaries
    """
    results = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip aggregated rows
            if row['Name'] == 'Aggregated':
                continue
            
            results.append({
                'name': row['Name'],
                'method': row['Type'],
                'request_count': int(row['Request Count']),
                'failure_count': int(row['Failure Count']),
                'median': float(row['Median Response Time']),
                'average': float(row['Average Response Time']),
                'min': float(row['Min Response Time']),
                'max': float(row['Max Response Time']),
                'p50': float(row['50%']),
                'p66': float(row['66%']),
                'p75': float(row['75%']),
                'p80': float(row['80%']),
                'p90': float(row['90%']),
                'p95': float(row['95%']),
                'p98': float(row['98%']),
                'p99': float(row['99%']),
                'p100': float(row['100%']),
                'rps': float(row['Requests/s']),
                'failures_per_s': float(row['Failures/s'])
            })
    
    return results


def classify_endpoint(name: str, method: str) -> str:
    """
    Classify endpoint type for threshold selection
    
    Args:
        name: Endpoint name
        method: HTTP method
    
    Returns:
        Endpoint classification
    """
    if method == 'POST':
        return 'POST'
    elif method == 'GET':
        # Check if it's a complex query
        if 'search' in name.lower() and any(x in name.lower() for x in ['filter', 'multi', 'complex']):
            return 'GET_COMPLEX'
        else:
            return 'GET_SIMPLE'
    else:
        return 'OTHER'


def check_thresholds(results: List[Dict]) -> Tuple[List[str], List[str]]:
    """
    Check results against performance thresholds
    
    Args:
        results: List of result dictionaries
    
    Returns:
        Tuple of (passed checks, failed checks)
    """
    passed = []
    failed = []
    
    for result in results:
        name = result['name']
        endpoint_type = classify_endpoint(name, result['method'])
        
        # Calculate error rate
        total_requests = result['request_count'] + result['failure_count']
        error_rate = (result['failure_count'] / total_requests * 100) if total_requests > 0 else 0
        
        # Check error rate
        if error_rate <= PerformanceThresholds.ERROR_RATE:
            passed.append(f"✓ {name}: Error rate {error_rate:.2f}% <= {PerformanceThresholds.ERROR_RATE}%")
        else:
            failed.append(f"✗ {name}: Error rate {error_rate:.2f}% > {PerformanceThresholds.ERROR_RATE}%")
        
        # Check response times based on endpoint type
        if endpoint_type == 'GET_SIMPLE':
            if result['average'] <= PerformanceThresholds.GET_SIMPLE_AVG:
                passed.append(f"✓ {name}: Avg response time {result['average']:.0f}ms <= {PerformanceThresholds.GET_SIMPLE_AVG}ms")
            else:
                failed.append(f"✗ {name}: Avg response time {result['average']:.0f}ms > {PerformanceThresholds.GET_SIMPLE_AVG}ms")
            
            if result['p95'] <= PerformanceThresholds.GET_SIMPLE_P95:
                passed.append(f"✓ {name}: 95th percentile {result['p95']:.0f}ms <= {PerformanceThresholds.GET_SIMPLE_P95}ms")
            else:
                failed.append(f"✗ {name}: 95th percentile {result['p95']:.0f}ms > {PerformanceThresholds.GET_SIMPLE_P95}ms")
        
        elif endpoint_type == 'GET_COMPLEX':
            if result['average'] <= PerformanceThresholds.GET_COMPLEX_AVG:
                passed.append(f"✓ {name}: Avg response time {result['average']:.0f}ms <= {PerformanceThresholds.GET_COMPLEX_AVG}ms")
            else:
                failed.append(f"✗ {name}: Avg response time {result['average']:.0f}ms > {PerformanceThresholds.GET_COMPLEX_AVG}ms")
            
            if result['p95'] <= PerformanceThresholds.GET_COMPLEX_P95:
                passed.append(f"✓ {name}: 95th percentile {result['p95']:.0f}ms <= {PerformanceThresholds.GET_COMPLEX_P95}ms")
            else:
                failed.append(f"✗ {name}: 95th percentile {result['p95']:.0f}ms > {PerformanceThresholds.GET_COMPLEX_P95}ms")
        
        elif endpoint_type == 'POST':
            if result['average'] <= PerformanceThresholds.POST_AVG:
                passed.append(f"✓ {name}: Avg response time {result['average']:.0f}ms <= {PerformanceThresholds.POST_AVG}ms")
            else:
                failed.append(f"✗ {name}: Avg response time {result['average']:.0f}ms > {PerformanceThresholds.POST_AVG}ms")
            
            if result['p95'] <= PerformanceThresholds.POST_P95:
                passed.append(f"✓ {name}: 95th percentile {result['p95']:.0f}ms <= {PerformanceThresholds.POST_P95}ms")
            else:
                failed.append(f"✗ {name}: 95th percentile {result['p95']:.0f}ms > {PerformanceThresholds.POST_P95}ms")
        
        # Check RPS
        if result['rps'] >= PerformanceThresholds.MIN_RPS:
            passed.append(f"✓ {name}: RPS {result['rps']:.2f} >= {PerformanceThresholds.MIN_RPS}")
        else:
            failed.append(f"✗ {name}: RPS {result['rps']:.2f} < {PerformanceThresholds.MIN_RPS}")
    
    return passed, failed


def print_results(results: List[Dict], passed: List[str], failed: List[str]):
    """
    Print formatted results
    
    Args:
        results: List of result dictionaries
        passed: List of passed checks
        failed: List of failed checks
    """
    print("=" * 80)
    print("PERFORMANCE THRESHOLD CHECK RESULTS")
    print("=" * 80)
    print()
    
    # Print summary statistics
    print("SUMMARY STATISTICS")
    print("-" * 80)
    for result in results:
        total_requests = result['request_count'] + result['failure_count']
        error_rate = (result['failure_count'] / total_requests * 100) if total_requests > 0 else 0
        
        print(f"\n{result['name']} ({result['method']})")
        print(f"  Requests: {result['request_count']:,}")
        print(f"  Failures: {result['failure_count']:,} ({error_rate:.2f}%)")
        print(f"  RPS: {result['rps']:.2f}")
        print(f"  Response Times:")
        print(f"    Average: {result['average']:.0f}ms")
        print(f"    Median: {result['median']:.0f}ms")
        print(f"    95th percentile: {result['p95']:.0f}ms")
        print(f"    99th percentile: {result['p99']:.0f}ms")
        print(f"    Max: {result['max']:.0f}ms")
    
    print()
    print("=" * 80)
    print("THRESHOLD CHECKS")
    print("=" * 80)
    print()
    
    # Print passed checks
    if passed:
        print("PASSED CHECKS:")
        print("-" * 80)
        for check in passed:
            print(check)
        print()
    
    # Print failed checks
    if failed:
        print("FAILED CHECKS:")
        print("-" * 80)
        for check in failed:
            print(check)
        print()
    
    # Print overall result
    print("=" * 80)
    total_checks = len(passed) + len(failed)
    pass_rate = (len(passed) / total_checks * 100) if total_checks > 0 else 0
    
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {len(passed)} ({pass_rate:.1f}%)")
    print(f"Failed: {len(failed)} ({100 - pass_rate:.1f}%)")
    print()
    
    if not failed:
        print("✓ ALL PERFORMANCE THRESHOLDS MET!")
    else:
        print("✗ SOME PERFORMANCE THRESHOLDS NOT MET")
    
    print("=" * 80)


def main():
    """Main execution"""
    if len(sys.argv) != 2:
        print("Usage: python check_performance_thresholds.py <locust_stats.csv>")
        print("Example: python check_performance_thresholds.py reports/load_test_results_stats.csv")
        return 1
    
    csv_path = sys.argv[1]
    
    try:
        # Load results
        results = load_results(csv_path)
        
        if not results:
            print("No results found in CSV file")
            return 1
        
        # Check thresholds
        passed, failed = check_thresholds(results)
        
        # Print results
        print_results(results, passed, failed)
        
        # Exit with appropriate code
        return 0 if not failed else 1
        
    except FileNotFoundError:
        print(f"Error: File not found: {csv_path}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
