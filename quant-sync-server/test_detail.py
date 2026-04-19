#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试 Obsidian API
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

print("=" * 60)
print("Detailed API Test")
print("=" * 60)

# 检查一个已知存在的文件
file_to_check = "Project-Overview.md"

print(f"\n1. GET /vault/{file_to_check}")
r = requests.get(f"{BASE_URL}/vault/{file_to_check}", headers=headers, verify=False)
print(f"   Status: {r.status_code}")
print(f"   Headers: {dict(r.headers)}")
print(f"   Content: {r.text[:1000]}")

print(f"\n2. GET /vault/{file_to_check} with Accept header")
r = requests.get(
    f"{BASE_URL}/vault/{file_to_check}",
    headers={
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'text/markdown',
    },
    verify=False
)
print(f"   Status: {r.status_code}")
print(f"   Content-Type: {r.headers.get('Content-Type')}")
print(f"   Content: {r.text[:500]}")

print(f"\n3. Check raw content directly")
r = requests.get(
    f"{BASE_URL}/vault/{file_to_check}",
    headers={'Authorization': f'Bearer {API_KEY}'},
    verify=False,
    stream=True
)
print(f"   Raw response length: {len(r.content)}")
print(f"   Raw content: {r.content[:500]}")

print("\n" + "=" * 60)
