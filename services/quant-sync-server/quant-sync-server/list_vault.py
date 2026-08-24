#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出 Obsidian Vault 中的文件
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
print("Obsidian Vault Contents")
print("=" * 60)

try:
    r = requests.get(f"{BASE_URL}/vault/", headers=headers, verify=False)
    if r.status_code == 200:
        data = r.json()
        files = data.get('files', [])
        print(f"\nTotal items: {len(files)}\n")
        for f in sorted(files):
            print(f"  {f}")
    else:
        print(f"Error: {r.status_code}")
        print(r.text)
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
