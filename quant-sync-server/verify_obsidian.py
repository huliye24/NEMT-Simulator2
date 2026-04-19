#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Obsidian 笔记内容
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

files = [
    "Project-Overview.md",
    "TechTree/Index.md",
    "WorkLog/Index.md",
    "NodeTasks/Index.md",
    "DesignSchemes/Index.md",
]

print("=" * 60)
print("Verifying Obsidian Notes")
print("=" * 60)

for f in files:
    print(f"\n--- {f} ---")
    try:
        r = requests.get(f"{BASE_URL}/vault/{f}", headers=headers, verify=False)
        if r.status_code == 200:
            content = r.text
            lines = content.split('\n')
            print('\n'.join(lines[:20]))
            if len(lines) > 20:
                print(f"... ({len(lines)} lines total)")
        else:
            print(f"Status: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
