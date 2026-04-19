#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 Notion 数据库内容的脚本
"""

import os
import sys
import json
import requests

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Database IDs from the URLs
DATABASE_IDS = [
    ("f5620ee6-b4e6-47f9-8420-f223cd6d808b", "Database 1"),
    ("de72f83c-b3c8-4b88-804e-92ce9cb738a2", "Database 2"),
    ("d679b710-2e5c-4714-a793-3fe260e6db37", "Database 3"),
    ("b84a2950-142c-49b8-9c5a-9ef876dbd933", "Database 4"),
]

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

def load_token():
    """从 .env 文件加载 token"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip().startswith('NOTION_TOKEN='):
                    return line.split('=', 1)[1].strip()
    return os.environ.get("NOTION_TOKEN", "")

def get_headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION,
    }

def extract_text_from_rich_text(rich_text):
    """从 rich_text 数组提取文本"""
    if not isinstance(rich_text, list):
        return ""
    return ''.join(item.get('text', {}).get('content', '') for item in rich_text if 'text' in item)

def extract_property_value(prop_name, prop_value):
    """提取属性值"""
    prop_type = prop_value.get('type', '')
    
    if prop_type == 'title':
        return extract_text_from_rich_text(prop_value.get('title', []))
    elif prop_type == 'rich_text':
        return extract_text_from_rich_text(prop_value.get('rich_text', []))
    elif prop_type == 'number':
        return prop_value.get('number')
    elif prop_type == 'checkbox':
        return prop_value.get('checkbox')
    elif prop_type == 'select':
        select = prop_value.get('select')
        return select.get('name') if select else None
    elif prop_type == 'multi_select':
        items = prop_value.get('multi_select', [])
        return [item.get('name') for item in items]
    elif prop_type == 'date':
        date = prop_value.get('date')
        return date.get('start') if date else None
    elif prop_type == 'url':
        return prop_value.get('url')
    elif prop_type == 'email':
        return prop_value.get('email')
    elif prop_type == 'phone_number':
        return prop_value.get('phone_number')
    elif prop_type == 'formula':
        formula = prop_value.get('formula')
        return formula.get('string') or formula.get('number') or formula.get('boolean')
    elif prop_type == 'relation':
        rels = prop_value.get('relation', [])
        return [r.get('id') for r in rels]
    elif prop_type == 'rollup':
        rollup = prop_value.get('rollup')
        return f"Rollup: {rollup.get('type', 'unknown')}"
    elif prop_type == 'created_time':
        return prop_value.get('created_time')
    elif prop_type == 'last_edited_time':
        return prop_value.get('last_edited_time')
    else:
        return f"[{prop_type}]"

def get_database_schema(db_id, headers):
    """获取数据库结构"""
    url = f"{BASE_URL}/databases/{db_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return None, f"Error: {response.status_code}"
    
    data = response.json()
    title = extract_text_from_rich_text(data.get('title', []))
    
    properties = {}
    for prop_name, prop_value in data.get('properties', {}).items():
        prop_type = prop_value.get('type', '')
        properties[prop_name] = prop_type
    
    return {'title': title, 'properties': properties}, None

def query_database(db_id, headers, max_items=10):
    """查询数据库内容"""
    url = f"{BASE_URL}/databases/{db_id}/query"
    
    results = []
    has_more = True
    start_cursor = None
    
    while has_more and len(results) < max_items:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            return None, f"Error querying: {response.status_code} - {response.text[:200]}"
        
        data = response.json()
        results.extend(data.get('results', []))
        has_more = data.get('has_more', False)
        start_cursor = data.get('next_cursor')
    
    return results[:max_items], None

def format_results(results, properties):
    """格式化查询结果"""
    if not results:
        return "  (No results)"
    
    formatted = []
    
    for i, item in enumerate(results):
        props = item.get('properties', {})
        formatted.append(f"\n  --- Item {i+1} ---")
        
        for prop_name in sorted(props.keys()):
            prop_value = props[prop_name]
            value = extract_property_value(prop_name, prop_value)
            if value:
                formatted.append(f"    {prop_name}: {value}")
    
    return '\n'.join(formatted)

def main():
    print("=" * 70)
    print("NEMT Simulator - Notion Database Fetcher")
    print("=" * 70)
    
    token = load_token()
    if not token:
        print("\n[ERROR] Notion token not found!")
        print("Please configure NOTION_TOKEN in quant-sync-server/.env")
        return
    
    print(f"\n[OK] Token found: {token[:15]}...")
    
    headers = get_headers(token)
    
    print("\n" + "-" * 70)
    print("Fetching Notion databases...")
    print("-" * 70 + "\n")
    
    for db_id, db_name in DATABASE_IDS:
        print(f"\n{'=' * 70}")
        print(f"Database: {db_name}")
        print(f"ID: {db_id}")
        print("=" * 70)
        
        # Get schema
        schema, error = get_database_schema(db_id, headers)
        if error:
            print(f"[ERROR] {error}")
            continue
        
        print(f"\n## Title: {schema['title']}")
        print(f"URL: https://notion.so/{db_id.replace('-', '')}")
        
        print("\n### Schema:")
        print("-" * 40)
        for prop_name, prop_type in sorted(schema['properties'].items()):
            print(f"  - {prop_name}: {prop_type}")
        
        # Query data
        results, error = query_database(db_id, headers)
        if error:
            print(f"\n[ERROR] {error}")
            continue
        
        print(f"\n### Data (showing {len(results)} of {len(results)} items):")
        print("-" * 40)
        print(format_results(results, schema['properties']))
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)

if __name__ == "__main__":
    main()
