#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取指定 Notion 页面内容
"""

import os
import sys
import json
import requests

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

def get_headers():
    return {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Content-Type': 'application/json',
        'Notion-Version': NOTION_VERSION,
    }

def extract_text_from_rich_text(rich_text):
    if not isinstance(rich_text, list):
        return ""
    return ''.join(item.get('text', {}).get('content', '') for item in rich_text if 'text' in item)

def get_page_content(page_id, headers):
    """获取页面内容"""
    blocks_url = f"{BASE_URL}/blocks/{page_id}/children?page_size=100"
    response = requests.get(blocks_url, headers=headers)
    
    if response.status_code != 200:
        return None, f"Error: {response.status_code}"
    
    blocks = response.json().get('results', [])
    content = []
    
    for block in blocks:
        block_type = block.get('type', 'unknown')
        block_content = block.get(block_type, {})
        text = extract_text_from_rich_text(block_content.get('rich_text', []))
        
        if block_type == 'heading_1':
            content.append(f"\n# {text}\n")
        elif block_type == 'heading_2':
            content.append(f"\n## {text}\n")
        elif block_type == 'heading_3':
            content.append(f"\n### {text}\n")
        elif block_type == 'paragraph':
            if text:
                content.append(text)
        elif block_type == 'bulleted_list_item':
            content.append(f"- {text}")
        elif block_type == 'numbered_list_item':
            content.append(f"1. {text}")
        elif block_type == 'to_do':
            checked = block_content.get('checked', False)
            status = "[x]" if checked else "[ ]"
            content.append(f"- {status} {text}")
        elif block_type == 'code':
            language = block_content.get('language', '')
            content.append(f"\n```{language}\n{text}\n```\n")
        elif block_type == 'quote':
            content.append(f"> {text}")
        elif block_type == 'callout':
            emoji = block.get('callout', {}).get('icon', {}).get('emoji', '')
            content.append(f"\n> {emoji} {text}\n")
        elif block_type == 'divider':
            content.append("\n---\n")
        elif block_type == 'image':
            image_url = block_content.get('external', {}).get('url') or block_content.get('file', {}).get('url', '')
            if image_url:
                content.append(f"\n![image]({image_url})\n")
        elif block_type == 'toggle':
            content.append(f"\n**{text}** (click to expand)")
        else:
            if text:
                content.append(f"[{block_type}]: {text}")
    
    return '\n'.join(content), None

def get_database_content(db_id, headers):
    """获取数据库内容"""
    url = f"{BASE_URL}/databases/{db_id}/query"
    results = []
    has_more = True
    
    while has_more:
        response = requests.post(url, headers=headers, json={"page_size": 100})
        if response.status_code != 200:
            return None, f"Error: {response.status_code}"
        
        data = response.json()
        results.extend(data.get('results', []))
        has_more = data.get('has_more', False)
    
    items = []
    for item in results:
        props = item.get('properties', {})
        item_data = {}
        for name, prop in props.items():
            prop_type = prop.get('type', '')
            if prop_type == 'title':
                item_data[name] = extract_text_from_rich_text(prop.get('title', []))
            elif prop_type == 'rich_text':
                item_data[name] = extract_text_from_rich_text(prop.get('rich_text', []))
            elif prop_type == 'number':
                item_data[name] = prop.get('number')
            elif prop_type == 'checkbox':
                item_data[name] = prop.get('checkbox')
            elif prop_type == 'select':
                select = prop.get('select')
                item_data[name] = select.get('name') if select else None
            elif prop_type == 'multi_select':
                item_data[name] = [m.get('name') for m in prop.get('multi_select', [])]
            elif prop_type == 'date':
                date = prop.get('date')
                item_data[name] = date.get('start') if date else None
        items.append(item_data)
    
    return items, None

def main():
    pages = [
        ("34617dca0dd28001a7e0db624dd5cf31", "Page 1"),
        ("34617dca0dd280f4a717df949596f424", "Page 2"),
    ]
    
    headers = get_headers()
    all_content = []
    
    for page_id, name in pages:
        all_content.append(f"\n{'='*60}")
        all_content.append(f"Fetching: {name}")
        all_content.append(f"ID: {page_id}")
        all_content.append("="*60)
        
        content, error = get_page_content(page_id, headers)
        
        if error:
            # Try as database
            items, error = get_database_content(page_id, headers)
            if error:
                all_content.append(f"Error: {error}")
            else:
                all_content.append(f"\nDatabase items ({len(items)}):")
                for i, item in enumerate(items):
                    all_content.append(f"\n--- Item {i+1} ---")
                    for k, v in item.items():
                        if v:
                            all_content.append(f"  {k}: {v}")
        else:
            all_content.append(content)
    
    # Save to file
    output_file = os.path.join(os.path.dirname(__file__), 'notion_pages_content.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_content))
    
    print(f"Content saved to: {output_file}")

if __name__ == "__main__":
    main()
