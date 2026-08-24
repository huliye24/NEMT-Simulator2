#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 Notion 页面内容
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

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

def load_token():
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

def extract_text(rich_text):
    if not isinstance(rich_text, list):
        return ""
    return ''.join(item.get('text', {}).get('content', '') for item in rich_text if 'text' in item)

def get_page(page_id, headers):
    """获取页面元数据"""
    url = f"{BASE_URL}/pages/{page_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_blocks(block_id, headers):
    """获取块内容"""
    url = f"{BASE_URL}/blocks/{block_id}/children?page_size=100"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def format_block(block):
    block_type = block.get('type', 'unknown')
    block_content = block.get(block_type, {})
    
    if block_type == 'heading_1':
        text = extract_text(block_content.get('rich_text', []))
        return f"\n# {text}\n" if text else ""
    elif block_type == 'heading_2':
        text = extract_text(block_content.get('rich_text', []))
        return f"\n## {text}\n" if text else ""
    elif block_type == 'heading_3':
        text = extract_text(block_content.get('rich_text', []))
        return f"\n### {text}\n" if text else ""
    elif block_type == 'paragraph':
        text = extract_text(block_content.get('rich_text', []))
        return text if text else ""
    elif block_type == 'bulleted_list_item':
        text = extract_text(block_content.get('rich_text', []))
        return f"- {text}" if text else ""
    elif block_type == 'numbered_list_item':
        text = extract_text(block_content.get('rich_text', []))
        return f"1. {text}" if text else ""
    elif block_type == 'to_do':
        checked = block_content.get('checked', False)
        text = extract_text(block_content.get('rich_text', []))
        status = "[x]" if checked else "[ ]"
        return f"- {status} {text}" if text else ""
    elif block_type == 'code':
        language = block_content.get('language', '')
        text = extract_text(block_content.get('rich_text', []))
        return f"\n```{language}\n{text}\n```\n" if text else ""
    elif block_type == 'quote':
        text = extract_text(block_content.get('rich_text', []))
        return f"> {text}" if text else ""
    elif block_type == 'callout':
        emoji = block.get('callout', {}).get('icon', {}).get('emoji', '')
        text = extract_text(block_content.get('rich_text', []))
        return f"> {emoji} {text}" if text else ""
    elif block_type == 'divider':
        return "\n---\n"
    elif block_type == 'child_database':
        title = block_content.get('title', [])
        db_title = extract_text(title) if title else block.get('id', '')
        return f"\n[Database: {db_title}]\n"
    elif block_type == 'child_page':
        title = block_content.get('title', [])
        page_title = extract_text(title) if title else block.get('id', '')
        return f"\n[Page: {page_title}]\n"
    else:
        return ""

def main():
    token = load_token()
    if not token:
        print("ERROR: NOTION_TOKEN not found")
        return
    
    headers = get_headers(token)
    
    pages = [
        "34617dca0dd28001a7e0db624dd5cf31",
        "34617dca0dd280f4a717df949596f424",
    ]
    
    for page_id in pages:
        print(f"\n{'='*60}")
        print(f"Page: {page_id}")
        print("="*60)
        
        blocks = get_blocks(page_id, headers)
        
        for block in blocks:
            formatted = format_block(block)
            if formatted:
                print(formatted)
        
        print()

if __name__ == "__main__":
    main()
