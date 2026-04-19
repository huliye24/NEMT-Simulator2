#!/usr/bin/env python3
"""Fetch Notion page content using requests"""

import os
import sys
import requests
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check for Notion token
notion_token = os.environ.get("NOTION_TOKEN")
if not notion_token:
    env_path = os.path.join(os.path.dirname(__file__), "quant-sync-server", ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                if line.startswith("NOTION_TOKEN="):
                    notion_token = line.split("=", 1)[1].strip()
                    break

if not notion_token:
    print("NOTION_TOKEN not found!")
    sys.exit(1)

page_id = "34717dca0dd28089954ecbee6d59ca35"

def fetch_page():
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    page = response.json()
    print("=" * 60)
    print("Page Info:")
    print("=" * 60)
    print(f"ID: {page.get('id')}")
    
    props = page.get('properties', {})
    for key, value in props.items():
        if value.get('type') == 'title':
            title = value.get('title', [{}])[0].get('plain_text', 'N/A')
            print(f"Title: {title}")
            break
    
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        sys.exit(1)
    
    blocks = response.json().get("results", [])
    
    print("\n" + "=" * 60)
    print("Page Content:")
    print("=" * 60)
    
    for block in blocks:
        block_type = block.get("type")
        
        def get_text(block_obj):
            rich_text = block_obj.get("rich_text", [])
            return "".join([t.get("plain_text", "") for t in rich_text])
        
        if block_type == "heading_1":
            content = get_text(block.get("heading_1", {}))
            print(f"\n# {content}")
            
        elif block_type == "heading_2":
            content = get_text(block.get("heading_2", {}))
            print(f"\n## {content}")
            
        elif block_type == "heading_3":
            content = get_text(block.get("heading_3", {}))
            print(f"\n### {content}")
            
        elif block_type == "paragraph":
            content = get_text(block.get("paragraph", {}))
            if content.strip():
                print(content)
                
        elif block_type == "bulleted_list_item":
            content = get_text(block.get("bulleted_list_item", {}))
            print(f"- {content}")
            
        elif block_type == "numbered_list_item":
            content = get_text(block.get("numbered_list_item", {}))
            print(f"1. {content}")
            
        elif block_type == "code":
            content = get_text(block.get("code", {}))
            lang = block.get("code", {}).get("language", "")
            print(f"\n```{lang}\n{content}\n```")
            
        elif block_type == "image":
            img_url = (block.get("image", {}).get("file", {}).get("url") or 
                      block.get("image", {}).get("external", {}).get("url", ""))
            print(f"\n![Image]({img_url})")
            
        elif block_type == "to_do":
            content = get_text(block.get("to_do", {}))
            checked = block.get("to_do", {}).get("checked", False)
            status = "[x]" if checked else "[ ]"
            print(f"- {status} {content}")
        
        elif block_type == "divider":
            print("\n---")
        
        elif block_type == "callout":
            content = get_text(block.get("callout", {}))
            icon = block.get("callout", {}).get("icon", {}).get("emoji", "")
            print(f"{icon} {content}")

if __name__ == "__main__":
    fetch_page()
