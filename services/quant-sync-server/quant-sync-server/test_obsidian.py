#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Obsidian API - 修复 Content-Type
"""

import os
import sys
import json
import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载配置
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

headers_no_content = {
    'Authorization': f'Bearer {API_KEY}',
}

print("=" * 60)
print("Testing Obsidian API - Creating Note")
print("=" * 60)

# 测试不同的 Content-Type
test_content = "# Test Note\n\nThis is a test created at " + str(__import__('datetime').datetime.now())

print("\n1. PUT with no Content-Type header")
try:
    r = requests.put(
        f"{BASE_URL}/vault/test-api.md",
        headers=headers_no_content,
        data=test_content,
        verify=False
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. PUT with text/markdown Content-Type")
try:
    headers_markdown = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'text/markdown',
    }
    r = requests.put(
        f"{BASE_URL}/vault/test-api2.md",
        headers=headers_markdown,
        data=test_content.encode('utf-8'),
        verify=False
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. PUT with application/json body")
try:
    headers_json = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {"content": test_content}
    r = requests.put(
        f"{BASE_URL}/vault/test-api3.md",
        headers=headers_json,
        json=payload,
        verify=False
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
