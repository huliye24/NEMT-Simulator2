#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试写入纯英文内容
"""

import os
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

content = """# Test Note

This is a test note.

## Section 1
Some content here.

## Section 2
More content.
"""

print("Writing English content...")
r = requests.put(
    f"{BASE_URL}/vault/test-english.md",
    headers=headers,
    data=content.encode('utf-8'),
    verify=False
)
print(f"Status: {r.status_code}")

# Read it back
print("\nReading back...")
r = requests.get(
    f"{BASE_URL}/vault/test-english.md",
    headers=headers,
    verify=False
)
print(f"Status: {r.status_code}")
print(f"Content: {r.text[:200]}")
print(f"Length: {len(r.text)}")
