#!/usr/bin/env python3
"""
System Monitoring Script for Load Testing

Monitors system resources during load tests and saves metrics to JSON.
Usage: python scripts/monitor_system.py --duration 600 --output reports/system_metrics.json
"""

import psutil
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any


class SystemMonitor:
    """Monitor system resources during load testing"""
    
    def __init__(self, interval: int = 5):
        """
        Initialize system monitor
        
        Args:
            interval: Sampling interval in seconds
        """
        self.interval = interval
        self.metrics: List[Dict[str, Any]] = []
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect current system metrics
        
        Returns:
            Dictionary with system metrics
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Process metrics (if running in Docker)
        process_count = len(psutil.pids())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency_mhz": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total_mb": memory.total / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024),
                "used_mb": memory.used / (1024 * 1024),
                "percent": memory.percent
            },
            "swap": {
                "total_mb": swap.total / (1024 * 1024),
                "used_mb": swap.used / (1024 * 1024),
                "percent": swap.percent
            },
            "disk": {
                "total_gb": disk.total / (1024 * 1024 * 1024),
                "used_gb": disk.used / (1024 * 1024 * 1024),
                "free_gb": disk.free / (1024 * 1024 * 1024),
                "percent": disk.percent
            },
            "disk_io": {
                "read_mb": disk_io.read_bytes / (1024 * 1024) if disk_io else None,
                "write_mb": disk_io.write_bytes / (1024 * 1024) if disk_io else None
            },
            "network": {
                "bytes_sent_mb": net_io.bytes_sent / (1024 * 1024),
                "bytes_recv_mb": net_io.bytes_recv / (1024 * 1024),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "processes": {
                "count": process_count
            }
        }
    
    def monitor(self, duration: int):
        """
        Monitor system for specified duration
        
        Args:
            duration: Monitoring duration in seconds
        """
        print(f"Starting system monitoring for {duration} seconds...")
        print(f"Sampling interval: {self.interval} seconds")
        print()
        
        start_time = time.time()
        end_time = start_time + duration
        sample_count = 0
        
        while time.time() < end_time:
            metrics = self.collect_metrics()
            self.metrics.append(metrics)
            sample_count += 1
            
            # Print progress
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            print(f"Sample {sample_count}: CPU {metrics['cpu']['percent']:.1f}%, "
                  f"Memory {metrics['memory']['percent']:.1f}%, "
                  f"Remaining: {remaining:.0f}s", end='\r')
            
            time.sleep(self.interval)
        
        print()
        print(f"\nMonitoring complete. Collected {sample_count} samples.")
    
    def save_metrics(self, output_path: str):
        """
        Save collected metrics to JSON file
        
        Args:
            output_path: Path to output JSON file
        """
        data = {
            "monitoring_info": {
                "start_time": self.metrics[0]["timestamp"] if self.metrics else None,
                "end_time": self.metrics[-1]["timestamp"] if self.metrics else None,
                "sample_count": len(self.metrics),
                "interval_seconds": self.interval
            },
            "metrics": self.metrics
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Metrics saved to {output_path}")
    
    def print_summary(self):
        """Print summary statistics"""
        if not self.metrics:
            print("No metrics collected")
            return
        
        # Calculate averages
        avg_cpu = sum(m['cpu']['percent'] for m in self.metrics) / len(self.metrics)
        max_cpu = max(m['cpu']['percent'] for m in self.metrics)
        
        avg_memory = sum(m['memory']['percent'] for m in self.metrics) / len(self.metrics)
        max_memory = max(m['memory']['percent'] for m in self.metrics)
        
        avg_disk = sum(m['disk']['percent'] for m in self.metrics) / len(self.metrics)
        
        print("\n" + "=" * 60)
        print("SYSTEM MONITORING SUMMARY")
        print("=" * 60)
        print(f"Samples collected: {len(self.metrics)}")
        print(f"Duration: {(len(self.metrics) * self.interval) / 60:.1f} minutes")
        print()
        print("CPU Usage:")
        print(f"  Average: {avg_cpu:.1f}%")
        print(f"  Maximum: {max_cpu:.1f}%")
        print()
        print("Memory Usage:")
        print(f"  Average: {avg_memory:.1f}%")
        print(f"  Maximum: {max_memory:.1f}%")
        print()
        print("Disk Usage:")
        print(f"  Average: {avg_disk:.1f}%")
        print()
        
        # Check against thresholds
        print("=" * 60)
        print("THRESHOLD CHECKS")
        print("=" * 60)
        
        if max_cpu < 80:
            print("✓ CPU usage within acceptable range (< 80%)")
        else:
            print(f"✗ CPU usage exceeded threshold ({max_cpu:.1f}% >= 80%)")
        
        if max_memory < 85:
            print("✓ Memory usage within acceptable range (< 85%)")
        else:
            print(f"✗ Memory usage exceeded threshold ({max_memory:.1f}% >= 85%)")
        
        print("=" * 60)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Monitor system resources during load testing')
    parser.add_argument('--duration', type=int, default=600,
                        help='Monitoring duration in seconds (default: 600)')
    parser.add_argument('--interval', type=int, default=5,
                        help='Sampling interval in seconds (default: 5)')
    parser.add_argument('--output', type=str, default='reports/system_metrics.json',
                        help='Output JSON file path (default: reports/system_metrics.json)')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = SystemMonitor(interval=args.interval)
    
    try:
        # Run monitoring
        monitor.monitor(duration=args.duration)
        
        # Print summary
        monitor.print_summary()
        
        # Save metrics
        monitor.save_metrics(args.output)
        
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user")
        if monitor.metrics:
            monitor.print_summary()
            monitor.save_metrics(args.output)
    except Exception as e:
        print(f"\n\nError during monitoring: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
