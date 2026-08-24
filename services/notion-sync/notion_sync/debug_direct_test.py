#!/usr/bin/env python3
"""Direct test of NotionSync from the module"""
import sys
import os

# Change to the server directory
os.chdir('/root/quant-sync-server')

# Now import the module
sys.path.insert(0, '/root/quant-sync-server')
from notion_sync_server import NotionSync, NotionClient

token = open('.env').read().strip().split('=')[1]

# Test NotionClient
print("=" * 60)
print("Testing NotionClient")
print("=" * 60)

client = NotionClient(token)
print(f"Client token: {token[:20]}...")

blocks = client.get_blocks('34317dca0dd280c9b1b4f1f0bbe7832c')
print(f"Blocks from get_blocks: {len(blocks)}")

child_ids = client.get_page_children_ids('34317dca0dd280c9b1b4f1f0bbe7832c')
print(f"Child IDs: {len(child_ids)}")
for cid in child_ids[:3]:
    print(f"  - {cid}")

# Test NotionSync
print("\n" + "=" * 60)
print("Testing NotionSync.sync_page")
print("=" * 60)

sync = NotionSync(token)
print(f"Sync initialized. Stats: {sync.stats}")

# Manually test one child
if child_ids:
    first_child = child_ids[0]
    print(f"\nSyncing first child: {first_child}")
    sync.sync_page(first_child, "")
    print(f"After sync. Stats: {sync.stats}")
