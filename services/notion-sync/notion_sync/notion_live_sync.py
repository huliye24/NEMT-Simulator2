#!/usr/bin/env python3
"""
Notion ↔ Obsidian 实时同步服务 (Watchdog + Polling)
===================================================
Notion → Obsidian 实时同步

功能:
- watchdog 文件监控 (Obsidian 变化检测)
- 定时轮询 Notion (检测 Notion 变化)
- systemd 守护进程支持
- 日志记录

使用方法:
    python notion_live_sync.py --daemon           # 守护进程模式
    python notion_live_sync.py --sync-once        # 单次同步
    python notion_live_sync.py --status            # 查看状态
    python notion_live_sync.py --stop              # 停止守护进程
"""

import os
import sys
import json
import time
import signal
import logging
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from threading import Thread, Event
from queue import Queue

import requests

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 尝试导入 watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

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

ROOT_PAGE_ID = "34317dca0dd280c9b1b4f1f0bbe7832c"
OBSIDIAN_ROOT = "/root/obsidian_vault"
OBSIDIAN_NEMT = "/root/obsidian_vault/NEMT_Notion"
OBSIDIAN_AGENT = "/root/obsidian_vault/NEMT_Agent_System"

STATE_FILE = "/root/quant-sync-server/live_sync_state.json"
PID_FILE = "/root/quant-sync-server/live_sync.pid"
LOG_FILE = "/root/quant-sync-server/live_sync.log"

POLL_INTERVAL = 180  # 3分钟检查一次 Notion
WATCH_FOLDERS = [OBSIDIAN_NEMT, OBSIDIAN_AGENT]

# ============================================================================
# 日志配置
# ============================================================================

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# 状态管理
# ============================================================================

def load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "pages": {},  # notion_id -> {hash, path, last_edited}
        "files": {},  # obsidian_path -> {hash, last_modified}
        "last_notion_sync": None,
        "last_obsidian_sync": None,
        "version": 2
    }

def save_state(state: Dict):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ============================================================================
# Notion API
# ============================================================================

class NotionClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data=None, params=None) -> Dict:
        url = f"{NOTION_API_BASE}/{endpoint}"
        try:
            if method == "POST":
                resp = requests.post(url, headers=self.headers, json=data or {}, params=params, timeout=30)
            elif method == "GET":
                resp = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method == "PATCH":
                resp = requests.patch(url, headers=self.headers, json=data, params=params, timeout=30)
            else:
                return {"error": "Unsupported method"}
            
            if resp.status_code >= 400:
                return {"error": f"{resp.status_code}: {resp.text[:200]}"}
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_page(self, page_id: str) -> Dict:
        return self._request("GET", f"pages/{page_id}")
    
    def get_blocks(self, block_id: str, page_size: int = 100) -> list:
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
    
    def get_page_children_ids(self, page_id: str) -> list:
        blocks = self.get_blocks(page_id)
        child_ids = []
        for block in blocks:
            block_type = block.get("type")
            if block_type in ("child_page", "child_database"):
                if block_type == "child_page":
                    child_id = block.get("id")
                else:
                    child_id = block.get(block_type, {}).get("id")
                if child_id:
                    child_ids.append(child_id)
        return child_ids

# ============================================================================
# 工具函数
# ============================================================================

def extract_title(page: Dict) -> str:
    for key, val in page.get("properties", {}).items():
        if val.get("type") == "title":
            texts = val.get("title", [])
            if texts:
                return "".join(t.get("plain_text", "") for t in texts)
    return page.get("id", "Untitled")[:8]

def extract_page_url(page: Dict) -> str:
    page_id = page.get("id", "").replace("-", "")
    return f"https://www.notion.so/{page_id}"

def sanitize_filename(name: str) -> str:
    if not name:
        return "untitled"
    invalid = '<>:"/\\|?*'
    for c in invalid:
        name = name.replace(c, '_')
    name = name.strip().strip('.')
    if len(name) > 150:
        name = name[:150]
    return name or "untitled"

def content_hash(content: str) -> str:
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# ============================================================================
# Notion → Obsidian 同步
# ============================================================================

class NotionToObsidianSync:
    def __init__(self, client: NotionClient, state: Dict):
        self.client = client
        self.state = state
        self.stats = {"synced": 0, "skipped": 0, "errors": 0, "new": 0}
    
    def sync(self, root_id: str = None) -> Dict:
        root_id = root_id or ROOT_PAGE_ID
        self.stats = {"synced": 0, "skipped": 0, "errors": 0, "new": 0}
        
        os.makedirs(OBSIDIAN_NEMT, exist_ok=True)
        
        self._sync_page(root_id, "")
        
        self.state["last_notion_sync"] = datetime.now().isoformat()
        save_state(self.state)
        
        return self.stats
    
    def _sync_page(self, page_id: str, parent_path: str):
        page = self.client.get_page(page_id)
        if "error" in page:
            logger.warning(f"获取页面失败: {page_id} - {page.get('error', '')[:100]}")
            self.stats["errors"] += 1
            return
        
        title = extract_title(page)
        safe_title = sanitize_filename(title)
        current_path = os.path.join(parent_path, safe_title) if parent_path else os.path.join(OBSIDIAN_NEMT, safe_title)
        md_path = os.path.join(current_path, f"{safe_title}.md")
        
        child_ids = self.client.get_page_children_ids(page_id)
        blocks = self.client.get_blocks(page_id)
        
        md_content = self._blocks_to_markdown(blocks)
        md_hash = content_hash(md_content)
        
        page_state = self.state["pages"].get(page_id, {})
        needs_sync = (
            page_id not in self.state["pages"] or
            page_state.get("content_hash") != md_hash
        )
        
        if needs_sync:
            frontmatter = self._build_frontmatter(page, extract_page_url(page), len(child_ids))
            self._write_md(md_path, md_content, frontmatter)
            self.state["pages"][page_id] = {
                "title": title,
                "path": md_path,
                "content_hash": md_hash,
                "last_edited": page.get("last_edited_time", ""),
            }
            self.stats["synced"] += 1
            self.stats["new" if page_id not in self.state["pages"] else "synced"] += 1
        else:
            self.stats["skipped"] += 1
        
        for child_id in child_ids:
            time.sleep(0.05)
            self._sync_page(child_id, current_path)
    
    def _blocks_to_markdown(self, blocks: list) -> str:
        lines = []
        for block in blocks:
            bt = block.get("type")
            if bt in ("child_page", "child_database"):
                continue
            content = block.get(bt, {})
            text = self._get_text(content)
            if not text.strip():
                continue
            if bt == "heading_1":
                lines.append(f"## {text}")
            elif bt == "heading_2":
                lines.append(f"### {text}")
            elif bt == "heading_3":
                lines.append(f"#### {text}")
            elif bt == "bulleted_list_item":
                lines.append(f"- {text}")
            elif bt == "numbered_list_item":
                lines.append(f"1. {text}")
            elif bt == "to_do":
                checked = "x" if content.get("checked") else " "
                lines.append(f"- [{checked}] {text}")
            elif bt == "code":
                lang = content.get("language", "")
                lines.append(f"```{lang}\n{text}\n```")
            elif bt == "quote":
                lines.append(f"> {text}")
            elif bt == "callout":
                icon = ""
                ic = content.get("icon", {})
                if ic.get("type") == "emoji":
                    icon = ic.get("emoji", "")
                lines.append(f"> {icon} {text}")
            elif bt == "divider":
                lines.append("---")
            elif bt == "paragraph":
                lines.append(text)
            lines.append("")
        return "\n".join(lines)
    
    def _get_text(self, content) -> str:
        if isinstance(content, dict):
            if "rich_text" in content:
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
                    link = rt.get("href")
                    if link:
                        t = f"[{t}]({link})"
                    parts.append(t)
                return "".join(parts)
            if "text" in content:
                return "".join(t.get("plain_text", "") for t in content["text"])
        elif isinstance(content, list):
            return "".join(t.get("plain_text", "") for t in content if isinstance(t, dict))
        return ""
    
    def _build_frontmatter(self, page: Dict, page_url: str, child_count: int) -> Dict:
        props = page.get("properties", {})
        fm = {
            "title": extract_title(page),
            "notion_id": page.get("id"),
            "notion_url": page_url,
            "created": page.get("created_time", "")[:10],
            "last_edited": page.get("last_edited_time", "")[:10],
            "synced": datetime.now().isoformat(),
        }
        for key, val in props.items():
            if key in ("名称", "Name", "title"):
                continue
            vt = val.get("type")
            if vt == "select":
                v = val.get("select", {}).get("name", "")
                if v: fm[key] = v
            elif vt == "multi_select":
                items = [s.get("name", "") for s in val.get("multi_select", [])]
                if items: fm[key] = items
            elif vt == "date":
                v = val.get("date", {}).get("start", "")
                if v: fm[key] = v
            elif vt == "checkbox":
                fm[key] = val.get("checkbox", False)
            elif vt == "number":
                fm[key] = val.get("number")
            elif vt == "url":
                v = val.get("url", "")
                if v: fm[key] = v
            elif vt == "rich_text":
                v = "".join(t.get("plain_text", "") for t in val.get("rich_text", []))
                if v: fm[key] = v
        if child_count > 0:
            fm["child_pages"] = child_count
        return fm
    
    def _write_md(self, path: str, content: str, frontmatter: Dict):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        lines = ["---"]
        for k, v in frontmatter.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for i in v:
                    lines.append(f"  - {i}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---\n")
        lines.append(content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

# ============================================================================
# Watchdog 文件监控
# ============================================================================

class ObsidianFileHandler(FileSystemEventHandler if HAS_WATCHDOG else object):
    """Obsidian 文件变化处理器"""
    
    def __init__(self, sync_queue: Queue):
        self.sync_queue = sync_queue
        self.ignore_patterns = {'.obsidian', '.git', '__pycache__', '.DS_Store'}
    
    def _should_ignore(self, path: str) -> bool:
        for pattern in self.ignore_patterns:
            if pattern in path:
                return True
        return False
    
    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_ignore(event.src_path):
            return
        if event.src_path.endswith('.md'):
            self.sync_queue.put(("modified", event.src_path))
    
    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_ignore(event.src_path):
            return
        if event.src_path.endswith('.md'):
            self.sync_queue.put(("created", event.src_path))
    
    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._should_ignore(event.src_path):
            return
        if event.src_path.endswith('.md'):
            self.sync_queue.put(("deleted", event.src_path))

# ============================================================================
# 守护进程
# ============================================================================

class SyncDaemon:
    def __init__(self, token: str, poll_interval: int = POLL_INTERVAL):
        self.token = token
        self.poll_interval = poll_interval
        self.client = NotionClient(token)
        self.state = load_state()
        self.running = True
        self.sync_queue = Queue()
        self.observer = None
        self.poll_thread = None
        self._start_time = datetime.now()
    
    def _save_pid(self):
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    
    def _remove_pid(self):
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    
    def signal_handler(self, signum, frame):
        logger.info("收到停止信号，正在关闭...")
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self._remove_pid()
        sys.exit(0)
    
    def start_watchdog(self):
        """启动 watchdog 文件监控"""
        if not HAS_WATCHDOG:
            logger.warning("watchdog 未安装，跳过文件监控")
            return
        
        handler = ObsidianFileHandler(self.sync_queue)
        self.observer = Observer()
        
        for folder in WATCH_FOLDERS:
            if os.path.exists(folder):
                self.observer.schedule(handler, folder, recursive=True)
                logger.info(f"监控文件夹: {folder}")
            else:
                logger.warning(f"文件夹不存在，跳过: {folder}")
        
        self.observer.start()
        logger.info("文件监控已启动")
    
    def poll_notion(self):
        """定时轮询 Notion"""
        logger.info(f"开始 Notion 轮询 (间隔: {self.poll_interval}秒)")
        
        while self.running:
            try:
                sync = NotionToObsidianSync(self.client, self.state)
                stats = sync.sync()
                
                if stats["synced"] > 0 or stats["new"] > 0:
                    logger.info(
                        f"Notion 同步完成: "
                        f"+{stats['new']} 新页面, "
                        f"~{stats['synced']-stats['new']} 更新, "
                        f"⏭ {stats['skipped']} 跳过, "
                        f"❌ {stats['errors']} 错误"
                    )
                else:
                    logger.debug(f"Notion 轮询完成: 无变化")
            
            except Exception as e:
                logger.error(f"Notion 轮询错误: {e}")
            
            if self.running:
                for remaining in range(self.poll_interval, 0, -30):
                    if not self.running:
                        break
                    time.sleep(30)
    
    def run(self):
        """运行守护进程"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self._save_pid()
        
        logger.info("=" * 60)
        logger.info("Notion ↔ Obsidian 实时同步服务启动")
        logger.info(f"Notion 根页面: {ROOT_PAGE_ID}")
        logger.info(f"Obsidian 目录: {OBSIDIAN_NEMT}")
        logger.info(f"轮询间隔: {self.poll_interval}秒")
        logger.info("=" * 60)
        
        # 初始同步
        logger.info("执行初始同步...")
        sync = NotionToObsidianSync(self.client, self.state)
        stats = sync.sync()
        logger.info(f"初始同步完成: +{stats['new']} 新, ~{stats['synced']-stats['new']} 更新, ⏭ {stats['skipped']} 跳过")
        
        # 启动 watchdog
        self.start_watchdog()
        
        # 启动轮询线程
        self.poll_thread = Thread(target=self.poll_notion, daemon=True)
        self.poll_thread.start()
        
        # 处理文件变化队列
        logger.info("守护进程运行中，按 Ctrl+C 停止")
        
        try:
            while self.running:
                try:
                    event = self.sync_queue.get(timeout=1)
                    action, path = event
                    logger.info(f"Obsidian 变化: [{action}] {path}")
                    # 这里可以添加 Obsidian → Notion 的反向同步逻辑
                except:
                    pass
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.observer:
                self.observer.stop()
                self.observer.join()
            self._remove_pid()
            logger.info("守护进程已停止")

# ============================================================================
# PID 管理
# ============================================================================

def get_running_pid() -> Optional[int]:
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return None

def is_running() -> bool:
    pid = get_running_pid()
    if pid:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            os.remove(PID_FILE)
    return False

def stop_daemon():
    pid = get_running_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"已发送停止信号到 PID {pid}")
            time.sleep(2)
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            return True
        except OSError as e:
            logger.error(f"停止失败: {e}")
            return False
    else:
        logger.error("守护进程未运行")
        return False

def status_daemon():
    pid = get_running_pid()
    state = load_state()
    
    print(f"\n{'='*60}")
    print(f"实时同步服务状态")
    print(f"{'='*60}")
    
    if is_running():
        print(f"状态: 运行中 (PID: {pid})")
    else:
        print(f"状态: 未运行")
    
    if state.get("last_notion_sync"):
        print(f"Notion 最后同步: {state['last_notion_sync']}")
    print(f"Notion 页面数: {len(state.get('pages', {}))}")
    print(f"状态文件: {STATE_FILE}")
    print(f"PID 文件: {PID_FILE}")
    print(f"日志文件: {LOG_FILE}")
    print(f"{'='*60}\n")

# ============================================================================
# 主函数
# ============================================================================

def main():
    global ROOT_PAGE_ID, POLL_INTERVAL
    
    parser = argparse.ArgumentParser(description="Notion ↔ Obsidian 实时同步")
    parser.add_argument("--daemon", action="store_true", help="守护进程模式")
    parser.add_argument("--sync-once", action="store_true", help="单次同步")
    parser.add_argument("--stop", action="store_true", help="停止守护进程")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--interval", type=int, default=POLL_INTERVAL, help=f"轮询间隔(秒)")
    parser.add_argument("--root", default=ROOT_PAGE_ID, help="Notion 根页面 ID")
    
    args = parser.parse_args()
    
    ROOT_PAGE_ID = args.root
    POLL_INTERVAL = args.interval
    
    if not NOTION_TOKEN:
        logger.error("未找到 NOTION_TOKEN")
        sys.exit(1)
    
    if args.stop:
        stop_daemon()
    elif args.status:
        status_daemon()
    elif args.sync_once:
        client = NotionClient(NOTION_TOKEN)
        state = load_state()
        sync = NotionToObsidianSync(client, state)
        stats = sync.sync()
        logger.info(f"同步完成: +{stats['new']} 新, ~{stats['synced']-stats['new']} 更新, ⏭ {stats['skipped']} 跳过, ❌ {stats['errors']} 错误")
    elif args.daemon:
        if is_running():
            logger.error("守护进程已在运行")
            sys.exit(1)
        daemon = SyncDaemon(NOTION_TOKEN, POLL_INTERVAL)
        daemon.run()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
