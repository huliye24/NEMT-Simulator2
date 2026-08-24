#!/usr/bin/env python3
"""Check sync status"""
import json
import os

state_file = "/root/quant-sync-server/live_sync_state.json"
if os.path.exists(state_file):
    with open(state_file) as f:
        d = json.load(f)
    pages = d.get("pages", {})
    print(f"Pages tracked: {len(pages)}")
    print(f"Last sync: {d.get('last_notion_sync', 'N/A')}")
else:
    print("State file not found")
