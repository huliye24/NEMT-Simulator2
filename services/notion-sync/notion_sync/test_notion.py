#!/usr/bin/env python3
"""测试 Notion API 连接"""
import requests
import os

token = os.environ.get('NOTION_TOKEN', '')
if not token:
    with open('/root/quant-sync-server/.env', 'r') as f:
        for line in f:
            if line.startswith('NOTION_TOKEN='):
                token = line.split('=', 1)[1].strip()
                break

headers = {
    'Authorization': f'Bearer {token}',
    'Notion-Version': '2022-06-28'
}

print("=" * 60)
print("Notion API 连接测试")
print("=" * 60)

# Test 1: Search
print("\n[1] 测试搜索 API...")
resp = requests.post('https://api.notion.com/v1/search', headers=headers, json={'query': 'NEMT'}, timeout=30)
data = resp.json()

if 'results' in data:
    print(f"    状态: OK")
    print(f"    找到 {len(data.get('results', []))} 个结果")
    print(f"    Has more: {data.get('has_more', False)}")
    for page in data.get('results', [])[:3]:
        title = page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'no title')
        ptype = page.get('object', 'unknown')
        print(f"    - [{ptype}] {title}")
else:
    print(f"    状态: Error - {data.get('message', 'Unknown error')}")

# Test 2: Get main page
print("\n[2] 测试获取页面...")
main_page_id = '34317dca0dd280c9b1b4f1f0bbe7832c'
resp2 = requests.get(f'https://api.notion.com/v1/pages/{main_page_id}', headers=headers, timeout=30)
if resp2.status_code == 200:
    title = resp2.json().get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'N/A')
    print(f"    状态: OK")
    print(f"    页面标题: {title}")
else:
    print(f"    状态: {resp2.status_code}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
