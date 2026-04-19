#!/usr/bin/env python3
"""
Benchmark script - runs on both local and remote machines
"""

import time
import json
import platform
import sys
import os
import math
import random

def get_system_info():
    """Get system information"""
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "cpu_count": os.cpu_count(),
    }
    
    try:
        import psutil
        info["memory_total_gb"] = psutil.virtual_memory().total / (1024**3)
        info["memory_available_gb"] = psutil.virtual_memory().available / (1024**3)
    except:
        pass
    
    return info

def benchmark_cpu_pi(digits=10000):
    """Calculate PI to benchmark CPU"""
    start = time.time()
    # Leibniz formula for PI
    pi = 0
    for i in range(1, digits * 100):
        pi += ((4.0 / (4 * i - 3)) - (4.0 / (4 * i - 1)))
    elapsed = time.time() - start
    return elapsed

def benchmark_cpu_sieve(n=100000):
    """Sieve of Eratosthenes to benchmark CPU"""
    start = time.time()
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    primes = sum(sieve)
    elapsed = time.time() - start
    return elapsed, primes

def benchmark_cpu_fibonacci(n=1000):
    """Fibonacci recursion benchmark"""
    def fib(n):
        if n < 2:
            return n
        return fib(n-1) + fib(n-2)
    
    start = time.time()
    result = fib(n)
    elapsed = time.time() - start
    return elapsed, result

def benchmark_memory_copy(size_mb=100):
    """Memory copy benchmark"""
    import copy
    size = size_mb * 1024 * 1024 // 8  # in 8-byte ints
    data = list(range(size))
    
    start = time.time()
    copied = copy.deepcopy(data)
    elapsed = time.time() - start
    
    return elapsed

def benchmark_cpu_matrix(size=500):
    """Matrix multiplication benchmark"""
    import numpy as np
    
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    
    start = time.time()
    c = np.dot(a, b)
    elapsed = time.time() - start
    
    return elapsed

def benchmark_file_io(file_size_mb=10):
    """File I/O benchmark"""
    import tempfile
    
    test_file = tempfile.NamedTemporaryFile(delete=False)
    test_file.close()
    
    # Write
    data = b'x' * (file_size_mb * 1024 * 1024)
    start = time.time()
    with open(test_file.name, 'wb') as f:
        f.write(data)
    write_time = time.time() - start
    
    # Read
    start = time.time()
    with open(test_file.name, 'rb') as f:
        f.read()
    read_time = time.time() - start
    
    # Cleanup
    os.unlink(test_file.name)
    
    return write_time, read_time

def benchmark_sha256(data_size=10):
    """SHA256 hashing benchmark"""
    import hashlib
    
    data = os.urandom(data_size * 1024 * 1024)
    
    start = time.time()
    for _ in range(10):
        hashlib.sha256(data).hexdigest()
    elapsed = time.time() - start
    
    return elapsed

def benchmark_sort(size=100000):
    """Sorting benchmark"""
    data = [random.random() for _ in range(size)]
    
    start = time.time()
    sorted_data = sorted(data)
    elapsed = time.time() - start
    
    return elapsed

def run_all_benchmarks():
    """Run all benchmarks"""
    print("=" * 60)
    print("Running Performance Benchmarks...")
    print("=" * 60)
    
    results = {}
    
    # System info
    print("\n[1/9] Getting system info...")
    results['system_info'] = get_system_info()
    
    # CPU PI
    print("[2/9] CPU PI calculation (10000 iterations)...")
    results['cpu_pi'] = benchmark_cpu_pi(10000)
    
    # CPU Sieve
    print("[3/9] CPU Sieve of Eratosthenes (100000)...")
    sieve_time, primes = benchmark_cpu_sieve(100000)
    results['cpu_sieve'] = sieve_time
    
    # CPU Fibonacci
    print("[4/9] CPU Fibonacci (n=30)...")
    fib_time, _ = benchmark_cpu_fibonacci(30)
    results['cpu_fibonacci'] = fib_time
    
    # Matrix multiplication
    print("[5/9] Matrix multiplication (500x500)...")
    try:
        results['cpu_matrix'] = benchmark_cpu_matrix(500)
    except:
        results['cpu_matrix'] = -1
        print("  (numpy not available, skipped)")
    
    # Memory copy
    print("[6/9] Memory copy (100MB)...")
    results['memory_copy'] = benchmark_memory_copy(100)
    
    # File I/O
    print("[7/9] File I/O (10MB)...")
    write_time, read_time = benchmark_file_io(10)
    results['file_write'] = write_time
    results['file_read'] = read_time
    
    # SHA256
    print("[8/9] SHA256 hashing (10MB x 10 iterations)...")
    results['sha256'] = benchmark_sha256(10)
    
    # Sorting
    print("[9/9] Sorting (100000 elements)...")
    results['sort'] = benchmark_sort(100000)
    
    return results

def save_results(results, filename):
    """Save results to JSON file"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NEMT Performance Benchmark")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.processor()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"CPU Cores: {os.cpu_count()}")
    print("=" * 60)
    
    results = run_all_benchmarks()
    save_results(results, 'benchmark_results.json')
    
    print("\n" + "=" * 60)
    print("Benchmark Complete!")
    print("=" * 60)
