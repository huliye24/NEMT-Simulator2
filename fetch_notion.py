#!/usr/bin/env python3
"""获取 Notion 页面内容"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

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
    blocks = []
    
    for block in data.get('results', []):
        block_type = block.get('type', '')
        content = block.get(block_type, {})
        text = extract_text(content.get('rich_text', []))
        
        blocks.append({
            'type': block_type,
            'text': text,
            'has_children': block.get('has_children', False)
        })
    
    return blocks

def print_blocks(blocks):
    """格式化打印 blocks"""
    for block in blocks:
        block_type = block['type']
        text = block['text']
        
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
        elif block_type == 'to_do':
            checked = content.get('checked', False)
            mark = '[x]' if checked else '[ ]'
            print(f"- {mark} {text}")
        elif block_type == 'code':
            language = content.get('language', '')
            print(f"\n```{language}\n{text}\n```")
        elif block_type == 'quote':
            print(f"\n> {text}")
        elif block_type == 'callout':
            icon = content.get('icon', {})
            icon_text = icon.get('emoji', '') if icon else ''
            print(f"\n> {icon_text} {text}")
        elif text:
            print(text)

if __name__ == '__main__':
    # 页面 ID
    pages = [
        ('架构设计', '34417dca0dd280099363e0b2d91ae0cc'),
        ('功能模块', '34417dca0dd280e98185dcdb24a06915'),
    ]
    
    for name, page_id in pages:
        print(f"\n{'='*60}")
        print(f"页面: {name}")
        print(f"{'='*60}\n")
        
        blocks = fetch_page_content(page_id)
        
        # 输出到文件
        with open(f'notion_page_{name}.txt', 'w', encoding='utf-8') as f:
            for block in blocks:
                block_type = block['type']
                text = block['text']
                f.write(f"[{block_type}] {text}\n")
        
        # 打印内容
        print_blocks(blocks)
        print(f"\n(内容已保存到 notion_page_{name}.txt)")
