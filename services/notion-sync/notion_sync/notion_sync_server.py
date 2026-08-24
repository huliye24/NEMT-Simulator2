#!/usr/bin/env python3
"""
Notion → Obsidian 实时同步服务
================================
从 Notion 页面同步到 Obsidian 本地仓库

功能:
- 从 Notion 根页面递归获取所有子页面
- 转换为 Markdown 格式并保存到 Obsidian
- 维护同步状态，支持增量更新
- 支持实时监控模式

使用方法:
    python notion_sync_server.py --sync-once      # 单次同步
    python notion_sync_server.py --daemon         # 守护进程模式
    python notion_sync_server.py --watch          # 文件监控模式
"""

import os
import sys
import json
import re
import hashlib
import time
import signal
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from threading import Thread
from queue import Queue
import argparse

import requests

# 确保 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# ============================================================================
# 配置
# ============================================================================

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    env_path = "/root/quant-sync-server/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('NOTION_TOKEN='):
                    NOTION_TOKEN = line.split('=', 1)[1].strip()
                    break

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Notion 根页面 ID
ROOT_PAGE_ID = "34317dca0dd280c9b1b4f1f0bbe7832c"  # NEMT 量化操作系统

# Obsidian 配置
OBSIDIAN_ROOT = "/root/obsidian_vault"
OBSIDIAN_NEMT = "/root/obsidian_vault/NEMT_Notion"

# 同步状态文件
STATE_FILE = "/root/quant-sync-server/sync_state.json"

# 配置文件
CONFIG_FILE = "/root/quant-sync-server/sync_config.json"

# 同步配置
SYNC_INTERVAL = 300  # 5分钟检查一次
BATCH_SIZE = 100

# ============================================================================
# 工具函数
# ============================================================================

def load_state() -> Dict:
    """加载同步状态"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"pages": {}, "last_sync": None, "version": 1}
    return {"pages": {}, "last_sync": None, "version": 1}

def save_state(state: Dict):
    """保存同步状态"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def sanitize_filename(name: str) -> str:
    """清理文件名"""
    if not name:
        return "untitled"
    invalid_chars = '<>:"/\\|?*'
    for c in invalid_chars:
        name = name.replace(c, '_')
    name = name.strip().strip('.')
    if len(name) > 150:
        name = name[:150]
    return name or "untitled"

def sanitize_path(name: str) -> str:
    """清理路径中的特殊字符"""
    return sanitize_filename(name)

# ============================================================================
# Notion API 客户端
# ============================================================================

class NotionClient:
    """Notion API 客户端"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                 params: Optional[Dict] = None) -> Dict:
        """发送请求"""
        url = f"{NOTION_API_BASE}/{endpoint}"
        try:
            if method == "POST":
                resp = requests.post(url, headers=self.headers, json=data or {}, params=params, timeout=30)
            elif method == "GET":
                resp = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method == "PATCH":
                resp = requests.patch(url, headers=self.headers, json=data, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if resp.status_code >= 400:
                print(f"[WARN] API Error {resp.status_code}: {resp.text[:200]}")
                return {"error": resp.text}
            
            return resp.json()
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            return {"error": str(e)}
    
    def get_page(self, page_id: str) -> Dict:
        """获取页面"""
        return self._request("GET", f"pages/{page_id}")
    
    def get_blocks(self, block_id: str, page_size: int = 100) -> List[Dict]:
        """获取块列表"""
        blocks = []
        cursor = None
        
        while True:
            params = {"page_size": page_size}
            if cursor:
                params["start_cursor"] = cursor
            
            result = self._request("GET", f"blocks/{block_id}/children", params=params)
            
            if "error" in result:
                break
            
            items = result.get("results", [])
            blocks.extend(items)
            
            if not result.get("has_more"):
                break
            
            cursor = result.get("next_cursor")
            if not cursor:
                break
            
            time.sleep(0.1)
        
        return blocks
    
    def search(self, query: str = "", filter_type: str = None) -> List[Dict]:
        """搜索页面"""
        data = {"query": query, "page_size": 100}
        if filter_type:
            data["filter"] = {"property": "object", "value": filter_type}
        
        result = self._request("POST", "search", data)
        
        if "error" in result:
            return []
        
        return result.get("results", [])
    
    def get_page_children_ids(self, page_id: str) -> List[str]:
        """获取页面的直接子页面 ID"""
        blocks = self.get_blocks(page_id)
        child_ids = []
        
        for block in blocks:
            block_type = block.get("type")
            if block_type in ("child_page", "child_database"):
                # child_page: ID 在顶层 block['id']
                # child_database: ID 在 block['child_database']['id']
                if block_type == "child_page":
                    child_id = block.get("id")
                else:
                    child_id = block.get(block_type, {}).get("id")
                if child_id:
                    child_ids.append(child_id)
        
        return child_ids

# ============================================================================
# 页面标题提取
# ============================================================================

def extract_title(page: Dict) -> str:
    """提取页面标题"""
    props = page.get("properties", {})
    
    for key, val in props.items():
        val_type = val.get("type")
        if val_type == "title":
            texts = val.get("title", [])
            if texts:
                return "".join(t.get("plain_text", "") for t in texts)
    
    return page.get("id", "Untitled")[:8]

def extract_page_url(page: Dict) -> str:
    """提取页面 URL"""
    page_id = page.get("id", "").replace("-", "")
    return f"https://www.notion.so/{page_id}"

# ============================================================================
# Notion 块转 Markdown
# ============================================================================

class BlockConverter:
    """Notion 块转 Markdown"""
    
    def __init__(self):
        self.indent_level = 0
    
    def blocks_to_markdown(self, blocks: List[Dict]) -> str:
        """块列表转 Markdown"""
        lines = []
        i = 0
        
        while i < len(blocks):
            block = blocks[i]
            block_type = block.get("type")
            content = block.get(block_type, {})
            
            # 跳过子页面引用
            if block_type in ("child_page", "child_database"):
                i += 1
                continue
            
            result = self._convert_block(block, content)
            if result:
                lines.append(result)
            
            i += 1
        
        return "\n".join(lines)
    
    def _convert_block(self, block: Dict, content: Any) -> str:
        """转换单个块"""
        block_type = block.get("type")
        
        converters = {
            "paragraph": self._convert_paragraph,
            "heading_1": self._convert_heading1,
            "heading_2": self._convert_heading2,
            "heading_3": self._convert_heading3,
            "bulleted_list_item": self._convert_bullet,
            "numbered_list_item": self._convert_numbered,
            "to_do": self._convert_todo,
            "toggle": self._convert_toggle,
            "code": self._convert_code,
            "quote": self._convert_quote,
            "callout": self._convert_callout,
            "divider": self._convert_divider,
            "image": self._convert_image,
            "table": self._convert_table,
            "table_row": self._convert_table_row,
            "embed": self._convert_embed,
            "bookmark": self._convert_bookmark,
            "link_preview": self._convert_link_preview,
            "video": self._convert_video,
            "audio": self._convert_audio,
            "file": self._convert_file,
            "pdf": self._convert_pdf,
            "column_list": self._pass,
            "column": self._pass,
            "synced_block": self._pass,
            "template": self._pass,
            "link_to_page": self._pass,
            "breadcrumb": self._pass,
        }
        
        converter = converters.get(block_type, self._convert_unsupported)
        return converter(block, content)
    
    def _get_text(self, content: Any) -> str:
        """提取文本内容"""
        if isinstance(content, dict):
            if "rich_text" in content:
                return "".join(t.get("plain_text", "") for t in content["rich_text"])
            if "text" in content:
                return "".join(t.get("plain_text", "") for t in content["text"])
        elif isinstance(content, list):
            return "".join(t.get("plain_text", "") for t in content if isinstance(t, dict))
        return ""
    
    def _get_annotations(self, content: Any) -> str:
        """获取文本格式"""
        text = self._get_text(content)
        if not text:
            return text
        
        if isinstance(content, dict) and "rich_text" in content:
            parts = []
            for rt in content["rich_text"]:
                t = rt.get("plain_text", "")
                ann = rt.get("annotations", {})
                if ann.get("code"):
                    t = f"`{t}`"
                if ann.get("bold"):
                    t = f"**{t}**"
                if ann.get("italic"):
                    t = f"*{t}*"
                if ann.get("strikethrough"):
                    t = f"~~{t}~~"
                if ann.get("underline"):
                    t = f"<u>{t}</u>"
                
                link = rt.get("href")
                if link:
                    t = f"[{t}]({link})"
                
                parts.append(t)
            return "".join(parts)
        
        return text
    
    def _convert_paragraph(self, block, content):
        text = self._get_annotations(content)
        return f"{text}\n" if text.strip() else ""
    
    def _convert_heading1(self, block, content):
        return f"## {self._get_annotations(content)}\n"
    
    def _convert_heading2(self, block, content):
        return f"### {self._get_annotations(content)}\n"
    
    def _convert_heading3(self, block, content):
        return f"#### {self._get_annotations(content)}\n"
    
    def _convert_bullet(self, block, content):
        return f"- {self._get_annotations(content)}"
    
    def _convert_numbered(self, block, content):
        return f"1. {self._get_annotations(content)}"
    
    def _convert_todo(self, block, content):
        checked = "x" if content.get("checked") else " "
        return f"- [{checked}] {self._get_annotations(content)}"
    
    def _convert_toggle(self, block, content):
        text = self._get_annotations(content)
        return f"<details>\n<summary>{text}</summary>\n\n</details>"
    
    def _convert_code(self, block, content):
        lang = content.get("language", "")
        code = self._get_text(content)
        return f"```{lang}\n{code}\n```\n"
    
    def _convert_quote(self, block, content):
        text = self._get_annotations(content)
        return f"> {text}\n"
    
    def _convert_callout(self, block, content):
        icon = ""
        icon_data = content.get("icon")
        if icon_data:
            if icon_data.get("type") == "emoji":
                icon = icon_data.get("emoji", "")
            elif icon_data.get("type") == "external":
                icon = f"![icon]({icon_data.get('external', {}).get('url', '')})"
            elif icon_data.get("type") == "file":
                icon = f"![icon]({icon_data.get('file', {}).get('url', '')})"
        
        text = self._get_annotations(content)
        return f"> {icon} {text}\n"
    
    def _convert_divider(self, block, content):
        return "---\n"
    
    def _convert_image(self, block, content):
        url = ""
        caption = self._get_text(content.get("caption", []))
        
        if content.get("type") == "external":
            url = content.get("external", {}).get("url", "")
        elif content.get("type") == "file":
            url = content.get("file", {}).get("url", "")
        
        if url:
            return f"![{caption}]({url})\n"
        return ""
    
    def _convert_table(self, block, content):
        return ""
    
    def _convert_table_row(self, block, content):
        cells = content.get("cells", [])
        row = "| " + " | ".join(self._get_text(cell) for cell in cells) + " |"
        return row
    
    def _convert_embed(self, block, content):
        url = content.get("url", "")
        return f"[embed]({url})\n"
    
    def _convert_bookmark(self, block, content):
        url = content.get("url", "")
        caption = self._get_text(content.get("caption", []))
        return f"[{caption or url}]({url})\n"
    
    def _convert_link_preview(self, block, content):
        url = content.get("url", "")
        return f"[link]({url})\n"
    
    def _convert_video(self, block, content):
        if content.get("type") == "external":
            url = content.get("external", {}).get("url", "")
        elif content.get("type") == "file":
            url = content.get("file", {}).get("url", "")
        else:
            url = ""
        return f"![video]({url})\n" if url else ""
    
    def _convert_audio(self, block, content):
        if content.get("type") == "external":
            url = content.get("external", {}).get("url", "")
        elif content.get("type") == "file":
            url = content.get("file", {}).get("url", "")
        else:
            url = ""
        return f"[audio]({url})\n" if url else ""
    
    def _convert_file(self, block, content):
        if content.get("type") == "external":
            url = content.get("external", {}).get("url", "")
        elif content.get("type") == "file":
            url = content.get("file", {}).get("url", "")
        else:
            url = ""
        name = self._get_text(content.get("caption", [])) or "file"
        return f"[{name}]({url})\n" if url else ""
    
    def _convert_pdf(self, block, content):
        if content.get("type") == "external":
            url = content.get("external", {}).get("url", "")
        elif content.get("type") == "file":
            url = content.get("file", {}).get("url", "")
        else:
            url = ""
        return f"[PDF]({url})\n" if url else ""
    
    def _convert_unsupported(self, block, content):
        text = self._get_text(content)
        if text:
            return text
        return ""
    
    def _pass(self, block, content):
        return ""

# ============================================================================
# 同步器
# ============================================================================

class NotionSync:
    """Notion → Obsidian 同步器"""
    
    def __init__(self, token: str):
        self.client = NotionClient(token)
        self.converter = BlockConverter()
        self.state = load_state()
        self.stats = {"synced": 0, "skipped": 0, "errors": 0}
    
    def _get_content_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _build_frontmatter(self, page: Dict, page_url: str, child_count: int = 0) -> Dict:
        """构建 frontmatter"""
        props = page.get("properties", {})
        fm = {
            "title": extract_title(page),
            "notion_id": page.get("id"),
            "notion_url": page_url,
            "created": page.get("created_time", "")[:10],
            "last_edited": page.get("last_edited_time", "")[:10],
            "synced": datetime.now().isoformat(),
            "tags": [],
        }
        
        # 添加属性
        for key, val in props.items():
            if key in ("名称", "Name", "title"):
                continue
            val_type = val.get("type")
            
            if val_type == "select":
                v = val.get("select", {}).get("name", "")
                if v:
                    fm[key] = v
            elif val_type == "multi_select":
                items = [s.get("name", "") for s in val.get("multi_select", [])]
                if items:
                    fm[key] = items
            elif val_type == "date":
                v = val.get("date", {}).get("start", "")
                if v:
                    fm[key] = v
            elif val_type == "checkbox":
                fm[key] = val.get("checkbox", False)
            elif val_type == "number":
                fm[key] = val.get("number")
            elif val_type == "url":
                v = val.get("url", "")
                if v:
                    fm[key] = v
            elif val_type == "rich_text":
                v = "".join(t.get("plain_text", "") for t in val.get("rich_text", []))
                if v:
                    fm[key] = v
        
        if child_count > 0:
            fm["child_pages"] = child_count
        
        return fm
    
    def _write_markdown(self, file_path: str, content: str, frontmatter: Dict):
        """写入 Markdown 文件"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        lines = ["---"]
        for key, val in frontmatter.items():
            if isinstance(val, list):
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {val}")
        lines.append("---\n")
        lines.append(content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    def _page_to_file_path(self, page: Dict, parent_path: str = "") -> str:
        """页面转文件路径"""
        title = extract_title(page)
        safe_title = sanitize_filename(title)
        
        if parent_path:
            return os.path.join(parent_path, f"{safe_title}.md")
        return os.path.join(OBSIDIAN_NEMT, f"{safe_title}.md")
    
    def _should_sync(self, page_id: str, content_hash: str) -> bool:
        """判断是否需要同步"""
        page_state = self.state["pages"].get(page_id, {})
        
        if page_id not in self.state["pages"]:
            return True
        
        if page_state.get("content_hash") != content_hash:
            return True
        
        return False
    
    def sync_page(self, page_id: str, parent_path: str = "") -> bool:
        """同步单个页面"""
        # 获取页面
        page = self.client.get_page(page_id)
        if "error" in page:
            print(f"  [ERROR] Failed to get page {page_id}: {page.get('error', '')[:100]}")
            self.stats["errors"] += 1
            return False
        
        title = extract_title(page)
        page_url = extract_page_url(page)
        
        # 获取子页面数量
        child_ids = self.client.get_page_children_ids(page_id)
        
        # 构建路径
        safe_title = sanitize_filename(title)
        current_path = os.path.join(parent_path, safe_title) if parent_path else os.path.join(OBSIDIAN_NEMT, safe_title)
        md_path = os.path.join(current_path, f"{safe_title}.md")
        
        # 获取内容
        blocks = self.client.get_blocks(page_id)
        content = self.converter.blocks_to_markdown(blocks)
        content_hash = self._get_content_hash(content)
        
        # 检查是否需要同步
        page_state = self.state["pages"].get(page_id, {})
        
        needs_sync = (
            page_id not in self.state["pages"] or
            page_state.get("content_hash") != content_hash
        )
        
        if not needs_sync:
            print(f"  ⏭️  {title} (未变化)")
            self.stats["skipped"] += 1
        else:
            # 构建 frontmatter
            frontmatter = self._build_frontmatter(page, page_url, len(child_ids))
            
            # 确保目录存在
            os.makedirs(current_path, exist_ok=True)
            
            # 写入文件
            self._write_markdown(md_path, content, frontmatter)
            
            # 更新状态
            self.state["pages"][page_id] = {
                "title": title,
                "path": md_path,
                "content_hash": content_hash,
                "last_edited": page.get("last_edited_time", ""),
            }
            
            print(f"  ✅ {title}")
            self.stats["synced"] += 1
        
        # 递归同步子页面
        for child_id in child_ids:
            time.sleep(0.1)  # 避免 API 限制
            self.sync_page(child_id, current_path)
        
        return True
    
    def sync_all(self) -> Dict:
        """同步所有页面"""
        print(f"\n{'='*60}")
        print(f"🔄 Notion → Obsidian 同步")
        print(f"{'='*60}")
        print(f"📂 Obsidian: {OBSIDIAN_NEMT}")
        print(f"🌐 Notion: {ROOT_PAGE_ID}")
        print()
        
        self.stats = {"synced": 0, "skipped": 0, "errors": 0}
        
        # 确保目标目录存在
        os.makedirs(OBSIDIAN_NEMT, exist_ok=True)
        
        # 从根页面开始同步
        start_time = time.time()
        self.sync_page(ROOT_PAGE_ID)
        
        # 更新状态
        self.state["last_sync"] = datetime.now().isoformat()
        save_state(self.state)
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"📊 同步完成 ({elapsed:.1f}s)")
        print(f"   ✅ 已同步/更新: {self.stats['synced']}")
        print(f"   ⏭️  跳过: {self.stats['skipped']}")
        print(f"   ❌ 错误: {self.stats['errors']}")
        print(f"   📁 总页面: {len(self.state['pages'])}")
        print(f"{'='*60}")
        
        return self.stats

# ============================================================================
# 守护进程模式
# ============================================================================

class SyncDaemon:
    """同步守护进程"""
    
    def __init__(self, token: str, interval: int = 300):
        self.sync = NotionSync(token)
        self.interval = interval
        self.running = True
        self.last_sync_time = None
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        print("\n[INFO] 收到停止信号，正在关闭...")
        self.running = False
    
    def run(self):
        """运行守护进程"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"🚀 启动同步守护进程")
        print(f"   同步间隔: {self.interval} 秒")
        print(f"   按 Ctrl+C 停止\n")
        
        while self.running:
            self.sync.sync_all()
            self.last_sync_time = datetime.now()
            
            if self.running:
                print(f"\n💤 下次同步: {self.interval} 秒后...")
                for remaining in range(self.interval, 0, -10):
                    if not self.running:
                        break
                    time.sleep(10)
                    print(f"\r    {remaining}s... ", end="", flush=True)
                print()
        
        print("[INFO] 守护进程已停止")

# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Notion → Obsidian 同步服务")
    parser.add_argument("--sync-once", action="store_true", help="单次同步")
    parser.add_argument("--daemon", action="store_true", help="守护进程模式")
    parser.add_argument("--interval", type=int, default=SYNC_INTERVAL, help=f"同步间隔(秒，默认{SYNC_INTERVAL})")
    parser.add_argument("--root", default=ROOT_PAGE_ID, help="Notion 根页面 ID")
    
    args = parser.parse_args()
    
    if not NOTION_TOKEN:
        print("❌ 错误: 未找到 NOTION_TOKEN")
        print(f"请在 {env_path} 配置")
        sys.exit(1)
    
    # 创建同步器
    sync = NotionSync(NOTION_TOKEN)
    
    if args.sync_once:
        sync.sync_all()
    elif args.daemon:
        daemon = SyncDaemon(NOTION_TOKEN, args.interval)
        daemon.run()
    else:
        # 默认单次同步
        sync.sync_all()

if __name__ == "__main__":
    main()
