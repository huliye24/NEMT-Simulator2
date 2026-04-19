#!/usr/bin/env python3
"""获取 Notion 页面内容 - 简化版"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# 设置 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

# 加载环境变量
load_dotenv('quant-sync-server/.env')

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
HEADERS = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

def extract_text(rich_text):
    """从 rich_text 数组提取纯文本"""
    if not rich_text:
        return ""
    return "".join([t.get('plain_text', '') for t in rich_text])

def fetch_page_content(page_id):
    """获取页面内容"""
    url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return []
    
    data = response.json()
    return data.get('results', [])

def print_block(block):
    """打印单个 block"""
    block_type = block.get('type', '')
    content = block.get(block_type, {})
    text = extract_text(content.get('rich_text', []))
    
    if block_type == 'heading_1':
        print(f"\n# {text}")
    elif block_type == 'heading_2':
        print(f"\n## {text}")
    elif block_type == 'heading_3':
        print(f"\n### {text}")
    elif block_type == 'bulleted_list_item':
        print(f"- {text}")
    elif block_type == 'numbered_list_item':
        print(f"1. {text}")
    elif block_type == 'code':
        language = content.get('language', '')
        print(f"\n```{language}\n{text}\n```")
    elif block_type == 'quote':
        print(f"\n> {text}")
    elif text:
        print(text)

if __name__ == '__main__':
    # 页面 ID
    pages = [
        ('初始架构-案例', '34617dca0dd280c89842ca75f3b44ca0'),
    ]
    
    for name, page_id in pages:
        print(f"\n{'='*60}")
        print(f"页面: {name}")
        print(f"{'='*60}\n")
        
        blocks = fetch_page_content(page_id)
        
        # 打印内容
        for block in blocks:
            print_block(block)
        
        print(f"\n(共 {len(blocks)} 个 block)")
