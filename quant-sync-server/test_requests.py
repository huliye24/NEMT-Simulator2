#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Python requests 库的写入方式
"""

import os
import sys
import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

env_path = os.path.join(os.path.dirname(__file__), 'obsidian.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")
BASE_URL = "https://127.0.0.1:27124"

headers = {'Authorization': f'Bearer {API_KEY}'}

content = "Test from Python requests at " + str(__import__('datetime').datetime.now())

print("=" * 60)
print("Testing Python requests")
print("=" * 60)

# Method 1: PUT with data as string
print("\n1. PUT with data as string:")
try:
    r = requests.put(
        f"{BASE_URL}/vault/requests-test1.md",
        headers=headers,
        data=content,
        verify=False
    )
    print(f"   Status: {r.status_code}")
except Exception as e:
    print(f"   Error: {e}")

# Read back
r = requests.get(f"{BASE_URL}/vault/requests-test1.md", headers=headers, verify=False)
print(f"   Read back: {r.text[:100]}")

# Method 2: PUT with data as bytes
print("\n2. PUT with data as bytes:")
try:
    r = requests.put(
        f"{BASE_URL}/vault/requests-test2.md",
        headers=headers,
        data=content.encode('utf-8'),
        verify=False
    )
    print(f"   Status: {r.status_code}")
except Exception as e:
    print(f"   Error: {e}")

# Read back
r = requests.get(f"{BASE_URL}/vault/requests-test2.md", headers=headers, verify=False)
print(f"   Read back: {r.text[:100]}")

# Method 3: PUT with json
print("\n3. PUT with json parameter:")
try:
    r = requests.put(
        f"{BASE_URL}/vault/requests-test3.md",
        headers=headers,
        json={"content": content},
        verify=False
    )
    print(f"   Status: {r.status_code}")
except Exception as e:
    print(f"   Error: {e}")

# Read back
r = requests.get(f"{BASE_URL}/vault/requests-test3.md", headers=headers, verify=False)
print(f"   Read back: {r.text[:100]}")

# Method 4: PUT with explicit Content-Type
print("\n4. PUT with explicit Content-Type text/plain:")
try:
    headers_ct = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'text/plain',
    }
    r = requests.put(
        f"{BASE_URL}/vault/requests-test4.md",
        headers=headers_ct,
        data=content.encode('utf-8'),
        verify=False
    )
    print(f"   Status: {r.status_code}")
except Exception as e:
    print(f"   Error: {e}")

# Read back
r = requests.get(f"{BASE_URL}/vault/requests-test4.md", headers=headers, verify=False)
print(f"   Read back: {r.text[:100]}")

# Method 5: session
print("\n5. PUT with session:")
try:
    session = requests.Session()
    session.headers.update(headers)
    r = session.put(
        f"{BASE_URL}/vault/requests-test5.md",
        data=content,
        verify=False
    )
    print(f"   Status: {r.status_code}")
except Exception as e:
    print(f"   Error: {e}")

# Read back
r = requests.get(f"{BASE_URL}/vault/requests-test5.md", headers=headers, verify=False)
print(f"   Read back: {r.text[:100]}")

print("\n" + "=" * 60)
