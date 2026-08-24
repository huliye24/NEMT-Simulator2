#!/usr/bin/env python3
import requests
import json

BASE = "http://localhost:8766"

# Test 1: system_info
print("=== Test 1: system_info ===")
r = requests.post(f"{BASE}/tools/call", json={"name": "system_info", "arguments": {}})
print(f"Status: {r.status_code}")
print(r.json())

# Test 2: file_list
print("\n=== Test 2: file_list ===")
r = requests.post(f"{BASE}/tools/call", json={"name": "file_list", "arguments": {"path": ".", "pattern": "*.py"}})
print(f"Status: {r.status_code}")
data = r.json()
print(data.get("result", {}).get("content", [{}])[0].get("text", "")[:500])

# Test 3: nemt_compute_dci
print("\n=== Test 3: nemt_compute_dci ===")
prices = [100, 102, 105, 103, 107, 110, 108, 112, 115, 113, 117, 120, 118, 122, 125, 123, 127, 130, 128, 132]
r = requests.post(f"{BASE}/tools/call", json={"name": "nemt_compute_dci", "arguments": {"prices": prices, "window": 14}})
print(f"Status: {r.status_code}")
data = r.json()
print(data.get("result", {}).get("content", [{}])[0].get("text", ""))

# Test 4: nemt_compute_resonance
print("\n=== Test 4: nemt_compute_resonance ===")
r = requests.post(f"{BASE}/tools/call", json={"name": "nemt_compute_resonance", "arguments": {"prices": prices, "threshold": 0.7}})
print(f"Status: {r.status_code}")
data = r.json()
print(data.get("result", {}).get("content", [{}])[0].get("text", ""))

# Test 5: nemt_get_signals
print("\n=== Test 5: nemt_get_signals ===")
r = requests.post(f"{BASE}/tools/call", json={"name": "nemt_get_signals", "arguments": {"prices": prices}})
print(f"Status: {r.status_code}")
data = r.json()
print(data.get("result", {}).get("content", [{}])[0].get("text", ""))

# Test 6: file_read
print("\n=== Test 6: file_read ===")
r = requests.post(f"{BASE}/tools/call", json={"name": "file_read", "arguments": {"path": "nemt_core.py", "max_lines": 20}})
print(f"Status: {r.status_code}")
data = r.json()
print(data.get("result", {}).get("content", [{}])[0].get("text", "")[:1000])

# Test 7: file_search
print("\n=== Test 7: file_search ===")
r = requests.post(f"{BASE}/tools/call", json={"name": "file_search", "arguments": {"path": ".", "pattern": "class NEMT", "file_pattern": "*.py"}})
print(f"Status: {r.status_code}")
data = r.json()
print(data.get("result", {}).get("content", [{}])[0].get("text", "")[:500])

print("\n=== All tests completed ===")
