#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理测试文件
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

test_files = [
    'test.md', 'test-api.md', 'test-api2.md', 'test-api3.md',
    'test-english.md', 'curl-test.md', 'chinese-test.md',
    'ps-test.md', 'ps-test2.md',
    'requests-test1.md', 'requests-test2.md', 'requests-test3.md',
    'requests-test4.md', 'requests-test5.md'
]

print("Cleaning up test files...")
for f in test_files:
    try:
        r = requests.delete(f"{BASE_URL}/vault/{f}", headers=headers, verify=False)
        if r.status_code == 204:
            print(f"  Deleted: {f}")
        else:
            print(f"  Not found: {f}")
    except:
        pass

print("Done!")
