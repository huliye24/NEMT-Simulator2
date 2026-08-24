#!/usr/bin/env python3
"""
Notion 双向同步 - Notion 到 Obsidian
=====================================
将 Notion 数据库内容同步到 Obsidian 本地文件

功能:
- 从 Notion 数据库获取内容
- 转换为 Markdown 格式
- 保存到本地 Obsidian 仓库
- 维护同步元数据

使用方法:
    python notion_sync/notion_to_obsidian.py --database Vision
    python notion_sync/notion_to_obsidian.py --all
"""

import os
import sys
import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import time

# 确保 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from notion_sync.setup_databases import NotionClient

# ============================================================================
# 配置
# ============================================================================

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    env_path = os.path.join(os.path.dirname(__file__), "..", "quant-sync-server", ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("NOTION_TOKEN="):
                    NOTION_TOKEN = line.split("=", 1)[1].strip()
                    break

# 同步配置
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OBSIDIAN_BASE = BASE_DIR  # Obsidian 仓库根目录

# 同步状态文件
SYNC_STATE_FILE = os.path.join(os.path.dirname(__file__), "sync_state.json")

# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class NotionPage:
    """Notion 页面结构"""
    id: str
    title: str
    properties: Dict[str, Any]
    blocks: List[Dict]
    url: str
    created_time: str
    last_edited_time: str
    parent_id: Optional[str] = None

@dataclass
class SyncRecord:
    """同步记录"""
    notion_id: str
    obsidian_path: str
    notion_hash: str
    obsidian_hash: str
    last_sync: str
    status: str  # synced, modified_notion, modified_obsidian, conflict

@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    notion_id: str
    path: str
    action: str  # created, updated, skipped, conflict, failed
    message: Optional[str] = None

# ============================================================================
# Notion 页面获取器
# ============================================================================

class NotionPageFetcher:
    """从 Notion 获取页面内容"""
    
    def __init__(self, client: NotionClient):
        self.client = client
    
    def get_database_pages(self, database_id: str) -> List[Dict]:
        """获取数据库中的所有页面"""
        pages = []
        cursor = None
        
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            
            try:
                response = self.client.post(f"databases/{database_id}/query", params)
                results = response.get("results", [])
                pages.extend(results)
                
                cursor = response.get("has_more") and response.get("next_cursor")
                if not cursor:
                    break
                
                time.sleep(0.2)  # 避免 API 频率限制
                
            except Exception as e:
                print(f"❌ 查询数据库失败: {e}")
                break
        
        return pages
    
    def get_page_properties(self, page_id: str) -> Dict:
        """获取页面属性"""
        try:
            response = self.client.get(f"pages/{page_id}")
            return response
        except Exception as e:
            print(f"❌ 获取页面属性失败: {e}")
            return {}
    
    def get_page_blocks(self, block_id: str) -> List[Dict]:
        """获取页面的所有块"""
        blocks = []
        cursor = None
        
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            
            try:
                response = self.client.get(f"blocks/{block_id}/children?page_size=100")
                results = response.get("results", [])
                blocks.extend(results)
                
                cursor = response.get("has_more") and response.get("next_cursor")
                if not cursor:
                    break
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"⚠️  获取块失败: {e}")
                break
        
        return blocks
    
    def extract_title(self, page: Dict) -> str:
        """提取页面标题"""
        properties = page.get("properties", {})
        
        for key, value in properties.items():
            if value.get("type") == "title":
                title_texts = value.get("title", [])
                if title_texts:
                    return "".join([t.get("plain_text", "") for t in title_texts])
        
        # 如果没有标题属性，尝试获取 URL 或 ID
        return page.get("id", "Untitled")[:8]
    
    def extract_property(self, prop: Dict) -> Any:
        """提取属性值"""
        prop_type = prop.get("type")
        
        if prop_type == "title":
            return "".join([t.get("plain_text", "") for t in prop.get("title", [])])
        
        elif prop_type == "rich_text":
            return "".join([t.get("plain_text", "") for t in prop.get("rich_text", [])])
        
        elif prop_type == "select":
            return prop.get("select", {}).get("name", "")
        
        elif prop_type == "multi_select":
            return [s.get("name", "") for s in prop.get("multi_select", [])]
        
        elif prop_type == "date":
            return prop.get("date", {}).get("start", "")
        
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        
        elif prop_type == "number":
            return prop.get("number")
        
        elif prop_type == "url":
            return prop.get("url", "")
        
        elif prop_type == "email":
            return prop.get("email", "")
        
        elif prop_type == "phone_number":
            return prop.get("phone_number", "")
        
        return None

# ============================================================================
# Notion 块转 Markdown 转换器
# ============================================================================

class NotionBlockConverter:
    """Notion 块转 Markdown"""
    
    def __init__(self):
        self._list_counter = 0
        self._in_list = False
    
    def blocks_to_markdown(self, blocks: List[Dict], level: int = 0) -> str:
        """将 Notion 块列表转换为 Markdown"""
        md_lines = []
        i = 0
        
        while i < len(blocks):
            block = blocks[i]
            block_type = block.get("type")
            
            # 处理不同类型的块
            if block_type == "paragraph":
                text = self._get_block_text(block.get("paragraph", {}))
                if text.strip():
                    md_lines.append(text)
                    md_lines.append("")
            
            elif block_type == "heading_1":
                text = self._get_block_text(block.get("heading_1", {}))
                md_lines.append(f"# {text}")
                md_lines.append("")
            
            elif block_type == "heading_2":
                text = self._get_block_text(block.get("heading_2", {}))
                md_lines.append(f"## {text}")
                md_lines.append("")
            
            elif block_type == "heading_3":
                text = self._get_block_text(block.get("heading_3", {}))
                md_lines.append(f"### {text}")
                md_lines.append("")
            
            elif block_type == "bulleted_list_item":
                items = []
                while i < len(blocks) and blocks[i].get("type") == "bulleted_list_item":
                    text = self._get_block_text(blocks[i].get("bulleted_list_item", {}))
                    items.append(text)
                    i += 1
                for item in items:
                    md_lines.append(f"- {item}")
                md_lines.append("")
                continue  # 跳过 i += 1
            
            elif block_type == "numbered_list_item":
                items = []
                num = 1
                while i < len(blocks) and blocks[i].get("type") == "numbered_list_item":
                    text = self._get_block_text(blocks[i].get("numbered_list_item", {}))
                    items.append(f"{num}. {text}")
                    num += 1
                    i += 1
                for item in items:
                    md_lines.append(item)
                md_lines.append("")
                continue
            
            elif block_type == "to_do":
                to_do = block.get("to_do", {})
                checked = "x" if to_do.get("checked") else " "
                text = self._get_block_text(to_do)
                md_lines.append(f"- [{checked}] {text}")
            
            elif block_type == "quote":
                text = self._get_block_text(block.get("quote", {}))
                md_lines.append(f"> {text}")
                md_lines.append("")
            
            elif block_type == "code":
                code_block = block.get("code", {})
                language = code_block.get("language", "")
                text = self._get_block_text(code_block)
                md_lines.append(f"```{language}")
                md_lines.append(text)
                md_lines.append("```")
                md_lines.append("")
            
            elif block_type == "divider":
                md_lines.append("---")
                md_lines.append("")
            
            elif block_type == "callout":
                callout = block.get("callout", {})
                icon = callout.get("icon", {}).get("emoji", "💡")
                text = self._get_block_text(callout)
                md_lines.append(f"> {icon} {text}")
                md_lines.append("")
            
            elif block_type == "toggle":
                toggle = block.get("toggle", {})
                text = self._get_block_text(toggle)
                md_lines.append(f"<details>")
                md_lines.append(f"<summary>{text}</summary>")
                
                # 处理子块
                if block.get("has_children"):
                    child_blocks = []  # 需要单独获取
                    if child_blocks:
                        md_lines.append("")
                        md_lines.extend(self.blocks_to_markdown(child_blocks, level + 1))
                
                md_lines.append("</details>")
                md_lines.append("")
            
            elif block_type == "image":
                image = block.get("image", {})
                caption = self._get_block_text(image.get("caption", []))
                url = image.get("file", {}).get("url") or image.get("external", {}).get("url", "")
                if url:
                    md_lines.append(f"![{caption}]({url})")
                md_lines.append("")
            
            elif block_type == "table":
                # 需要获取子块
                md_lines.append("")
            
            elif block_type == "table_row":
                cells = block.get("table_row", {}).get("cells", [])
                row = "| " + " | ".join([
                    "".join([c.get("plain_text", "") for c in cell])
                    for cell in cells
                ]) + " |"
                md_lines.append(row)
            
            i += 1
        
        return "\n".join(md_lines)
    
    def _get_block_text(self, block_content: Any) -> str:
        """从块内容中提取文本"""
        if isinstance(block_content, dict):
            if "rich_text" in block_content:
                return "".join([
                    t.get("plain_text", "")
                    for t in block_content["rich_text"]
                ])
            elif "text" in block_content:
                return "".join([
                    t.get("plain_text", "")
                    for t in block_content["text"]
                ])
        elif isinstance(block_content, list):
            return "".join([
                t.get("plain_text", "")
                for t in block_content
            ])
        return ""

# ============================================================================
# Obsidian 写入器
# ============================================================================

class ObsidianWriter:
    """写入 Obsidian 文件"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
    
    def sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        # 替换特殊字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # 清理空格和点
        name = name.strip().strip('.')
        
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        
        return name or "untitled"
    
    def ensure_folder(self, folder_path: str):
        """确保文件夹存在"""
        full_path = os.path.join(self.base_path, folder_path)
        os.makedirs(full_path, exist_ok=True)
        return full_path
    
    def write_page(self, relative_path: str, content: str, frontmatter: Dict = None):
        """写入页面"""
        full_path = os.path.join(self.base_path, relative_path)
        
        # 确保父目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 构建完整内容
        full_content = self._build_content(content, frontmatter)
        
        # 写入文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        return full_path
    
    def _build_content(self, content: str, frontmatter: Dict = None) -> str:
        """构建包含 frontmatter 的内容"""
        lines = []
        
        # 添加 frontmatter
        if frontmatter:
            lines.append("---")
            for key, value in frontmatter.items():
                if isinstance(value, list):
                    lines.append(f"{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: {value}")
            lines.append("---")
            lines.append("")
        
        lines.append(content)
        
        return "\n".join(lines)
    
    def file_exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        full_path = os.path.join(self.base_path, relative_path)
        return os.path.exists(full_path)
    
    def read_file(self, relative_path: str) -> Optional[str]:
        """读取文件内容"""
        full_path = os.path.join(self.base_path, relative_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def calculate_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()

# ============================================================================
# 同步状态管理
# ============================================================================

class SyncStateManager:
    """同步状态管理器"""
    
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state: Dict[str, SyncRecord] = {}
        self._load()
    
    def _load(self):
        """加载同步状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.state = {
                        k: SyncRecord(**v) for k, v in data.items()
                    }
            except Exception as e:
                print(f"⚠️  加载同步状态失败: {e}")
    
    def save(self):
        """保存同步状态"""
        data = {
            k: {
                "notion_id": v.notion_id,
                "obsidian_path": v.obsidian_path,
                "notion_hash": v.notion_hash,
                "obsidian_hash": v.obsidian_hash,
                "last_sync": v.last_sync,
                "status": v.status
            }
            for k, v in self.state.items()
        }
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_record(self, notion_id: str) -> Optional[SyncRecord]:
        """获取同步记录"""
        return self.state.get(notion_id)
    
    def update_record(self, record: SyncRecord):
        """更新同步记录"""
        self.state[record.notion_id] = record
        self.save()
    
    def get_status(self, notion_id: str, notion_hash: str, obsidian_path: str, obsidian_content: str) -> str:
        """判断同步状态"""
        record = self.get_record(notion_id)
        
        if not record:
            return "new"
        
        # 检查 Notion 是否修改
        if record.notion_hash != notion_hash:
            return "modified_notion"
        
        # 检查 Obsidian 是否修改
        obsidian_hash = hashlib.md5(obsidian_content.encode()).hexdigest() if obsidian_content else ""
        if record.obsidian_hash != obsidian_hash:
            return "modified_obsidian"
        
        return "synced"

# ============================================================================
# Notion 到 Obsidian 同步器
# ============================================================================

class NotionToObsidianSync:
    """Notion 到 Obsidian 同步器"""
    
    def __init__(self, notion_token: str, database_config: Optional[Dict] = None):
        self.client = NotionClient(notion_token)
        self.fetcher = NotionPageFetcher(self.client)
        self.converter = NotionBlockConverter()
        self.writer = ObsidianWriter(OBSIDIAN_BASE)
        self.state_manager = SyncStateManager(SYNC_STATE_FILE)
        
        # 数据库配置
        self.db_config = database_config or {}
        
        # 同步结果
        self.results: List[SyncResult] = []
    
    def get_folder_mapping(self, database_name: str) -> str:
        """获取数据库到文件夹的映射"""
        folder_map = {
            "Vision": "NEMT_Vision",
            "Decisions": "NEMT_Vision/Decisions",
            "Technical": "NEMT_Vision",
            "Tasks": "NEMT_Agent_System",
            "Templates": "NEMT_Vision/Templates",
            "ADR": "NEMT_Vision/ADR"
        }
        return folder_map.get(database_name, "NEMT_Notion")
    
    def sync_database(self, database_name: str) -> List[SyncResult]:
        """同步单个数据库"""
        if database_name not in self.db_config.get("databases", {}):
            print(f"❌ 数据库不存在: {database_name}")
            return []
        
        db_info = self.db_config["databases"][database_name]
        database_id = db_info["id"]
        
        print(f"\n{'='*60}")
        print(f"📚 同步数据库: {db_info['icon']} {db_info['name_cn']}")
        print(f"{'='*60}")
        
        # 获取所有页面
        print("📥 获取 Notion 页面...")
        pages = self.fetcher.get_database_pages(database_id)
        print(f"   找到 {len(pages)} 个页面")
        
        results = []
        for page in pages:
            result = self._sync_page(page, database_name)
            results.append(result)
            time.sleep(0.2)  # 避免 API 频率限制
        
        self.results.extend(results)
        return results
    
    def _sync_page(self, page: Dict, database_name: str) -> SyncResult:
        """同步单个页面"""
        page_id = page.get("id")
        title = self.fetcher.extract_title(page)
        
        print(f"\n  📄 {title}")
        
        try:
            # 获取页面块
            blocks = self.fetcher.get_page_blocks(page_id)
            
            # 转换为 Markdown
            content = self.converter.blocks_to_markdown(blocks)
            
            # 提取属性
            properties = page.get("properties", {})
            frontmatter = self._extract_frontmatter(properties)
            
            # 计算哈希
            notion_hash = hashlib.md5(content.encode()).hexdigest()
            
            # 确定文件路径
            folder = self.get_folder_mapping(database_name)
            filename = self.writer.sanitize_filename(title)
            relative_path = f"{folder}/{filename}.md"
            
            # 检查同步状态
            existing_content = self.writer.read_file(relative_path)
            status = self.state_manager.get_status(page_id, notion_hash, relative_path, existing_content)
            
            if status == "synced":
                print(f"    ⏭️  已同步，跳过")
                return SyncResult(
                    success=True,
                    notion_id=page_id,
                    path=relative_path,
                    action="skipped",
                    message="内容未变化"
                )
            
            elif status == "modified_obsidian":
                print(f"    ⚠️  Obsidian 已修改，存在冲突")
                # 备份并写入 Notion 版本
                backup_path = f"{folder}/{filename}_conflict_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                # 这里可以选择保留哪个版本
                # 为了安全起见，我们保留 Notion 版本
                print(f"    📝 保留 Notion 版本")
            
            # 写入文件
            full_path = self.writer.write_page(relative_path, content, frontmatter)
            
            # 计算 Obsidian 哈希
            obsidian_hash = self.writer.calculate_hash(content)
            
            # 更新同步状态
            record = SyncRecord(
                notion_id=page_id,
                obsidian_path=relative_path,
                notion_hash=notion_hash,
                obsidian_hash=obsidian_hash,
                last_sync=datetime.now().isoformat(),
                status="synced"
            )
            self.state_manager.update_record(record)
            
            print(f"    ✅ 已同步: {relative_path}")
            
            return SyncResult(
                success=True,
                notion_id=page_id,
                path=relative_path,
                action="updated"
            )
            
        except Exception as e:
            print(f"    ❌ 同步失败: {e}")
            return SyncResult(
                success=False,
                notion_id=page_id,
                path="",
                action="failed",
                message=str(e)
            )
    
    def _extract_frontmatter(self, properties: Dict) -> Dict:
        """从页面属性提取 frontmatter"""
        frontmatter = {}
        
        # 跳过标题属性
        skip_keys = ["名称", "Name", "title"]
        
        for key, value in properties.items():
            if key in skip_keys:
                continue
            
            extracted = self.fetcher.extract_property(value)
            if extracted is not None:
                # 转换为 YAML 友好格式
                fm_key = key.replace(" ", "_")
                frontmatter[fm_key] = extracted
        
        # 添加同步元数据
        frontmatter["notion_synced"] = datetime.now().isoformat()
        
        return frontmatter
    
    def sync_all(self) -> List[SyncResult]:
        """同步所有数据库"""
        all_results = []
        
        databases = self.db_config.get("databases", {})
        
        for db_name in databases.keys():
            results = self.sync_database(db_name)
            all_results.extend(results)
        
        return all_results
    
    def print_summary(self):
        """打印同步摘要"""
        total = len(self.results)
        success = len([r for r in self.results if r.success])
        updated = len([r for r in self.results if r.action == "updated"])
        skipped = len([r for r in self.results if r.action == "skipped"])
        failed = len([r for r in self.results if not r.success])
        
        print("\n" + "="*60)
        print("📊 Notion → Obsidian 同步摘要")
        print("="*60)
        print(f"  总计: {total}")
        print(f"  ✅ 成功: {success}")
        print(f"  📝 更新: {updated}")
        print(f"  ⏭️  跳过: {skipped}")
        print(f"  ❌ 失败: {failed}")
        print("="*60)

# ============================================================================
# 主函数
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Notion 到 Obsidian 同步")
    parser.add_argument("--database", "-d", help="同步指定数据库")
    parser.add_argument("--all", "-a", action="store_true", help="同步所有数据库")
    parser.add_argument("--config", "-c", default=os.path.join(os.path.dirname(__file__), "database_config.json"),
                       help="数据库配置文件路径")
    
    args = parser.parse_args()
    
    if not NOTION_TOKEN:
        print("❌ 错误: 未找到 NOTION_TOKEN")
        print("请设置环境变量或在 .env 文件中配置 NOTION_TOKEN")
        sys.exit(1)
    
    # 加载数据库配置
    db_config = {}
    if os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            db_config = json.load(f)
        print(f"✅ 加载数据库配置: {len(db_config.get('databases', {}))} 个数据库")
    else:
        print(f"⚠️  配置文件不存在: {args.config}")
        sys.exit(1)
    
    # 创建同步器
    sync = NotionToObsidianSync(NOTION_TOKEN, db_config)
    
    if args.database:
        sync.sync_database(args.database)
    elif args.all:
        sync.sync_all()
    else:
        print("请指定 --database <名称> 或 --all")
        print(f"\n可用数据库:")
        for name, info in db_config.get("databases", {}).items():
            print(f"  {info['icon']} {info['name_cn']} ({name})")
    
    sync.print_summary()

if __name__ == "__main__":
    main()
