#!/usr/bin/env python3
"""调试子页面获取"""
import requests
import os

token = open('/root/quant-sync-server/.env').read().strip().split('=')[1]
headers = {'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28'}

page_id = '34317dca0dd280c9b1b4f1f0bbe7832c'
resp = requests.get(f'https://api.notion.com/v1/blocks/{page_id}/children?page_size=100', headers=headers)
data = resp.json()

blocks = data.get('results', [])
print(f'Found {len(blocks)} blocks')
print(f'Has more: {data.get("has_more")}')

child_pages = [b for b in blocks if b.get('type') == 'child_page']
child_dbs = [b for b in blocks if b.get('type') == 'child_database']
print(f'Child pages: {len(child_pages)}')
print(f'Child databases: {len(child_dbs)}')

for cp in child_pages[:10]:
    cp_data = cp.get('child_page', {})
    print(f'  - {cp_data.get("title", "no title")} ({cp.get("id")})')

# Check first block type
if blocks:
    print(f'\nFirst block type: {blocks[0].get("type")}')
    print(f'First block: {blocks[0]}')
