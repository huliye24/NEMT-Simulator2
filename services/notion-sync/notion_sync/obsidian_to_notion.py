#!/usr/bin/env python3
"""
Notion 双向同步 - Obsidian 到 Notion
=====================================
将 Obsidian 文档同步到 Notion 数据库

功能:
- 解析 Obsidian Markdown 文件
- 转换为 Notion 块格式
- 创建/更新 Notion 页面
- 支持多种文档类型识别

使用方法:
    python notion_sync/obsidian_to_notion.py --folder NEMT_Vision
    python notion_sync/obsidian_to_notion.py --file NEMT_Vision/VISION.md
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 确保 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 导入设置模块
from notion_sync.setup_databases import NotionClient

# ============================================================================
# 配置
# ============================================================================

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    env_path = os.path.join(os.path.dirname(__file__), "..", "quant-sync-server", ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                if line.startswith("NOTION_TOKEN="):
                    NOTION_TOKEN = line.split("=", 1)[1].strip()
                    break

# 同步配置
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # 项目根目录
OBSIDIAN_FOLDERS = [
    "NEMT_Vision",
    "NEMT_Agent_System", 
    "TechLead_Resources",
    "NEMT_Notion"
]

# ============================================================================
# 文档类型枚举
# ============================================================================

class DocType(Enum):
    """文档类型枚举"""
    VISION = "Vision"           # 愿景文档
    DECISION = "Decisions"      # 决策记录
    TECHNICAL = "Technical"     # 技术文档
    TASK = "Tasks"             # 任务
    TEMPLATE = "Templates"      # 模板
    ADR = "ADR"                 # 架构决策记录
    UNKNOWN = "Unknown"         # 未知类型

@dataclass
class ObsidianDoc:
    """Obsidian 文档结构"""
    path: str                          # 文件路径
    relative_path: str                 # 相对于仓库根目录的路径
    title: str                         # 文档标题
    content: str                       # 原始内容
    doc_type: DocType                  # 文档类型
    frontmatter: Dict[str, Any]        # YAML frontmatter
    headings: List[str]                # 所有标题
    file_hash: str                     # 文件内容哈希
    last_modified: datetime             # 最后修改时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 其他元数据

@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    doc_path: str
    notion_id: Optional[str] = None
    error: Optional[str] = None
    action: str = "created"  # created, updated, skipped, failed

# ============================================================================
# Markdown 解析器
# ============================================================================

class MarkdownParser:
    """Markdown 文件解析器"""
    
    # Frontmatter 正则
    FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    
    # 标题正则
    HEADING_RE = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    # 代码块正则
    CODE_BLOCK_RE = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    
    # 列表项正则
    BULLET_LIST_RE = re.compile(r'^[\s]*[-*+]\s+(.+)$', re.MULTILINE)
    NUMBER_LIST_RE = re.compile(r'^[\s]*\d+\.\s+(.+)$', re.MULTILINE)
    
    # 表格正则
    TABLE_RE = re.compile(r'^\|(.+)\|[\s]*\n\|[-:\s]+\|[\s]*\n((?:\|.+\|[\s]*\n?)+)', re.MULTILINE)
    
    # 引用块正则
    QUOTE_RE = re.compile(r'^>\s*(.+)$', re.MULTILINE)
    
    # 分割线正则
    DIVIDER_RE = re.compile(r'^---+$', re.MULTILINE)
    
    # 任务列表正则
    TASK_RE = re.compile(r'^[\s]*-\s+\[([ xX])\]\s+(.+)$', re.MULTILINE)
    
    @classmethod
    def parse_frontmatter(cls, content: str) -> Tuple[Dict[str, Any], str]:
        """解析 YAML frontmatter"""
        match = cls.FRONTMATTER_RE.match(content)
        
        if match:
            frontmatter_str = match.group(1)
            body = content[match.end():]
            
            # 简单解析 YAML
            frontmatter = cls._parse_simple_yaml(frontmatter_str)
            return frontmatter, body
        
        return {}, content
    
    @staticmethod
    def _parse_simple_yaml(yaml_str: str) -> Dict[str, Any]:
        """简单 YAML 解析"""
        result = {}
        current_key = None
        
        for line in yaml_str.split('\n'):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            # 键值对
            if ':' in line and not line.startswith('-'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                if value:
                    result[key] = value
                else:
                    result[key] = None
                current_key = key
            
            # 列表项
            elif line.startswith('-'):
                value = line[1:].strip().strip('"\'')
                if current_key:
                    if result.get(current_key) is None:
                        result[current_key] = []
                    if isinstance(result[current_key], list):
                        result[current_key].append(value)
        
        return result
    
    @classmethod
    def extract_headings(cls, content: str) -> List[str]:
        """提取所有标题"""
        headings = []
        for match in cls.HEADING_RE.finditer(content):
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append(f"{'#' * level} {title}")
        return headings
    
    @classmethod
    def parse_file(cls, file_path: str, content: str) -> ObsidianDoc:
        """解析文件"""
        # 获取相对路径
        rel_path = os.path.relpath(file_path, BASE_DIR)
        
        # 解析 frontmatter
        frontmatter, body = cls.parse_frontmatter(content)
        
        # 提取标题
        headings = cls.extract_headings(content)
        
        # 获取文件名作为标题
        filename = os.path.splitext(os.path.basename(file_path))[0]
        title = filename
        
        # 从 frontmatter 或第一个标题获取标题
        if 'title' in frontmatter:
            title = frontmatter['title']
        elif headings:
            first_heading = headings[0]
            if first_heading.startswith('# '):
                title = first_heading[2:].strip()
        
        # 确定文档类型
        doc_type = cls._determine_doc_type(rel_path, title, frontmatter)
        
        # 计算文件哈希
        file_hash = hashlib.md5(content.encode()).hexdigest()
        
        # 获取最后修改时间
        mtime = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime)
        
        return ObsidianDoc(
            path=file_path,
            relative_path=rel_path,
            title=title,
            content=content,
            doc_type=doc_type,
            frontmatter=frontmatter,
            headings=headings,
            file_hash=file_hash,
            last_modified=last_modified,
            metadata={
                "filename": filename,
                "word_count": len(content.split()),
                "line_count": len(content.split('\n'))
            }
        )
    
    @staticmethod
    def _determine_doc_type(path: str, title: str, frontmatter: Dict) -> DocType:
        """确定文档类型"""
        path_lower = path.lower()
        title_lower = title.lower()
        
        # 根据路径判断
        if 'vision' in path_lower or '愿景' in path_lower:
            if 'decision' in path_lower or '决策' in path_lower:
                return DocType.DECISION
            return DocType.VISION
        
        if 'decision' in path_lower or 'adr' in path_lower or '决策' in path_lower:
            if 'adr' in path_lower:
                return DocType.ADR
            return DocType.DECISION
        
        if 'technical' in path_lower or 'tech' in path_lower or '技术' in path_lower:
            if 'debt' in path_lower:
                return DocType.TECHNICAL
            return DocType.TECHNICAL
        
        if 'task' in path_lower or '任务' in path_lower:
            return DocType.TASK
        
        if 'template' in path_lower or '模板' in path_lower:
            return DocType.TEMPLATE
        
        # 根据 frontmatter 判断
        if 'type' in frontmatter:
            type_str = frontmatter['type'].lower()
            if 'vision' in type_str:
                return DocType.VISION
            if 'decision' in type_str:
                return DocType.DECISION
            if 'technical' in type_str:
                return DocType.TECHNICAL
            if 'task' in type_str:
                return DocType.TASK
        
        # 根据标题判断
        if 'vision' in title_lower or '愿景' in title_lower:
            return DocType.VISION
        if 'decision' in title_lower or '决策' in title_lower:
            return DocType.DECISION
        if 'architecture' in title_lower or '架构' in title_lower:
            return DocType.TECHNICAL
        if 'task' in title_lower or '任务' in title_lower:
            return DocType.TASK
        
        return DocType.UNKNOWN

# ============================================================================
# Notion 块转换器
# ============================================================================

class NotionBlockConverter:
    """Markdown 转 Notion 块"""
    
    def __init__(self, max_children_per_page: int = 100):
        self.max_children = max_children_per_page
    
    def markdown_to_blocks(self, content: str) -> List[Dict]:
        """将 Markdown 内容转换为 Notion 块"""
        blocks = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 跳过 frontmatter
            if line.strip() == '---':
                # 跳过 frontmatter
                i += 1
                while i < len(lines) and lines[i].strip() != '---':
                    i += 1
                i += 1
                continue
            
            # 跳过空行
            if not line.strip():
                i += 1
                continue
            
            # 标题
            if line.startswith('#'):
                block = self._parse_heading(line)
                if block:
                    blocks.append(block)
                    i += 1
                    continue
            
            # 代码块
            if line.strip().startswith('```'):
                code_block, i = self._parse_code_block(lines, i)
                if code_block:
                    blocks.append(code_block)
                i += 1
                continue
            
            # 引用块
            if line.strip().startswith('>'):
                quote_text = self._parse_quote_block(lines, i)
                if quote_text:
                    blocks.append({
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": self._text_to_rich_text(quote_text)
                        }
                    })
                while i < len(lines) and lines[i].strip().startswith('>'):
                    i += 1
                continue
            
            # 分割线
            if re.match(r'^---+$', line.strip()):
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
                i += 1
                continue
            
            # 任务列表
            task_match = re.match(r'^[\s]*-\s+\[([ xX])\]\s+(.+)$', line)
            if task_match:
                checked = task_match.group(1).lower() == 'x'
                text = task_match.group(2)
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": self._text_to_rich_text(text),
                        "checked": checked
                    }
                })
                i += 1
                continue
            
            # 无序列表
            if re.match(r'^[\s]*[-*+]\s+', line):
                items, i = self._parse_bullet_list(lines, i)
                for item in items:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": self._text_to_rich_text(item)
                        }
                    })
                continue
            
            # 有序列表
            if re.match(r'^[\s]*\d+\.\s+', line):
                items, i = self._parse_number_list(lines, i)
                for item in items:
                    blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": self._text_to_rich_text(item)
                        }
                    })
                continue
            
            # 表格
            table_match = re.match(r'^\|(.+)\|$', line)
            if table_match and i + 1 < len(lines) and re.match(r'^\|[-:\s]+\|$', lines[i + 1]):
                table, i = self._parse_table(lines, i)
                if table:
                    blocks.extend(table)
                continue
            
            # 普通段落
            paragraph_text = self._parse_paragraph(lines, i)
            if paragraph_text:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": self._text_to_rich_text(paragraph_text)
                    }
                })
            i += 1
        
        return blocks
    
    def _text_to_rich_text(self, text: str) -> List[Dict]:
        """将文本转换为 rich_text 数组"""
        # 处理内联代码
        parts = []
        pattern = re.compile(r'`([^`]+)`')
        last_end = 0
        
        for match in pattern.finditer(text):
            # 添加匹配前的文本
            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    parts.append({
                        "type": "text",
                        "text": {"content": plain_text}
                    })
            
            # 添加代码
            parts.append({
                "type": "text",
                "text": {"content": match.group(1)},
                "annotations": {"code": True}
            })
            last_end = match.end()
        
        # 添加剩余文本
        if last_end < len(text):
            plain_text = text[last_end:]
            if plain_text:
                parts.append({
                    "type": "text",
                    "text": {"content": plain_text}
                })
        
        return parts if parts else [{"type": "text", "text": {"content": text}}]
    
    def _parse_heading(self, line: str) -> Optional[Dict]:
        """解析标题"""
        match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if not match:
            return None
        
        level = len(match.group(1))
        text = match.group(2)
        
        heading_types = {
            1: "heading_1",
            2: "heading_2", 
            3: "heading_3",
            4: "heading_4",
            5: "heading_5",
            6: "heading_6"
        }
        
        heading_type = heading_types.get(level, "heading_3")
        
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._text_to_rich_text(text)
            }
        }
    
    def _parse_code_block(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """解析代码块"""
        if start >= len(lines):
            return None, start
        
        first_line = lines[start].strip()
        if not first_line.startswith('```'):
            return None, start
        
        # 获取语言
        lang = first_line[3:].strip()
        
        code_lines = []
        i = start + 1
        while i < len(lines):
            if lines[i].strip().startswith('```'):
                break
            code_lines.append(lines[i])
            i += 1
        
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": self._text_to_rich_text('\n'.join(code_lines)),
                "language": lang if lang else "plain text"
            }
        }, i
    
    def _parse_quote_block(self, lines: List[str], start: int) -> str:
        """解析引用块"""
        quotes = []
        i = start
        while i < len(lines) and lines[i].strip().startswith('>'):
            quote = lines[i].strip()[1:].strip()
            quotes.append(quote)
            i += 1
        return ' '.join(quotes)
    
    def _parse_bullet_list(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """解析无序列表"""
        items = []
        i = start
        while i < len(lines):
            line = lines[i].strip()
            match = re.match(r'^[-*+]\s+(.+)$', line)
            if match:
                items.append(match.group(1))
                i += 1
            else:
                break
        return items, i
    
    def _parse_number_list(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """解析有序列表"""
        items = []
        i = start
        while i < len(lines):
            line = lines[i].strip()
            match = re.match(r'^\d+\.\s+(.+)$', line)
            if match:
                items.append(match.group(1))
                i += 1
            else:
                break
        return items, i
    
    def _parse_table(self, lines: List[str], start: int) -> Tuple[List[Dict], int]:
        """解析表格"""
        blocks = []
        
        # 解析表头
        header_line = lines[start]
        headers = [h.strip() for h in header_line.strip('|').split('|')]
        
        # 跳过分隔符
        i = start + 2
        
        # 解析数据行
        while i < len(lines):
            line = lines[i].strip()
            if not line.startswith('|'):
                break
            
            cells = [c.strip() for c in line.strip('|').split('|')]
            
            # 创建表格行
            for j, cell in enumerate(cells):
                cell_content = cell if j < len(headers) else ""
                blocks.append({
                    "object": "block",
                    "type": "table_row",
                    "table_row": {
                        "cells": [self._text_to_rich_text(cell_content)]
                    }
                })
            
            i += 1
        
        return blocks, i
    
    def _parse_paragraph(self, lines: List[str], start: int) -> str:
        """解析段落"""
        paragraph_lines = []
        i = start
        
        while i < len(lines):
            line = lines[i]
            
            # 遇到空行或特殊块结束
            if not line.strip():
                break
            
            # 遇到标题或代码块等特殊内容
            if line.strip().startswith('#') or line.strip().startswith('```'):
                break
            
            # 遇到引用块
            if line.strip().startswith('>'):
                break
            
            # 遇到分割线
            if re.match(r'^---+$', line.strip()):
                break
            
            # 遇到列表
            if re.match(r'^[\s]*[-*+]\s+', line):
                break
            if re.match(r'^[\s]*\d+\.\s+', line):
                break
            
            # 遇到任务列表
            if re.match(r'^[\s]*-\s+\[[ xX]\]\s+', line):
                break
            
            # 遇到表格
            if line.strip().startswith('|'):
                break
            
            paragraph_lines.append(line.strip())
            i += 1
            
            # 如果是单行引用块，后面没有内容就结束
            if not line.strip():
                break
        
        return ' '.join(paragraph_lines)

# ============================================================================
# Obsidian 到 Notion 同步器
# ============================================================================

class ObsidianToNotionSync:
    """Obsidian 到 Notion 同步器"""
    
    def __init__(self, notion_token: str, database_config: Optional[Dict] = None):
        self.client = NotionClient(notion_token)
        self.parser = MarkdownParser()
        self.converter = NotionBlockConverter()
        
        # 数据库配置
        self.db_config = database_config or {}
        
        # 同步记录
        self.sync_log: List[SyncResult] = []
    
    def scan_folder(self, folder_path: str) -> List[str]:
        """扫描文件夹中的所有 Markdown 文件"""
        files = []
        folder_full_path = os.path.join(BASE_DIR, folder_path)
        
        if not os.path.exists(folder_full_path):
            print(f"⚠️  目录不存在: {folder_full_path}")
            return files
        
        for root, _, filenames in os.walk(folder_full_path):
            for filename in filenames:
                if filename.endswith('.md'):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
        
        return sorted(files)
    
    def parse_document(self, file_path: str) -> Optional[ObsidianDoc]:
        """解析单个文档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parser.parse_file(file_path, content)
        
        except Exception as e:
            print(f"❌ 解析失败 {file_path}: {e}")
            return None
    
    def get_database_id(self, doc_type: DocType) -> Optional[str]:
        """获取文档类型对应的数据库 ID"""
        db_map = {
            DocType.VISION: "Vision",
            DocType.DECISION: "Decisions",
            DocType.TECHNICAL: "Technical",
            DocType.TASK: "Tasks",
            DocType.TEMPLATE: "Templates",
            DocType.ADR: "ADR",
        }
        
        db_name = db_map.get(doc_type)
        if db_name and db_name in self.db_config.get("databases", {}):
            return self.db_config["databases"][db_name]["id"]
        
        return None
    
    def create_page(self, doc: ObsidianDoc, parent_id: str) -> Optional[str]:
        """创建 Notion 页面"""
        try:
            # 构建页面属性
            properties = self._build_properties(doc)
            
            # 转换内容为块
            blocks = self.converter.markdown_to_blocks(doc.content)
            
            # 创建页面
            data = {
                "parent": {"database_id": parent_id},
                "properties": properties,
                "children": blocks[:100]  # Notion 限制每页最多 100 个子块
            }
            
            response = self.client.post("pages", data)
            page_id = response.get("id")
            
            if page_id:
                # 如果有更多块，分批添加
                if len(blocks) > 100:
                    self._append_blocks(page_id, blocks[100:])
                
                return page_id
            
            return None
        
        except Exception as e:
            print(f"❌ 创建页面失败: {e}")
            return None
    
    def _build_properties(self, doc: ObsidianDoc) -> Dict:
        """构建页面属性"""
        properties = {}
        
        # 标题
        properties["名称"] = {
            "title": [{"text": {"content": doc.title}}]
        }
        
        # 根据文档类型添加特定属性
        if doc.doc_type == DocType.VISION:
            properties["状态"] = {"select": {"name": "已批准"}}
            properties["类型"] = {"select": {"name": "愿景"}}
            properties["维护者"] = {"select": {"name": "Founder Agent"}}
        
        elif doc.doc_type == DocType.DECISION:
            # 从 frontmatter 获取日期
            date = doc.frontmatter.get("日期") or doc.frontmatter.get("date")
            if date:
                properties["日期"] = {"date": {"start": date}}
            properties["决策人"] = {"select": {"name": doc.frontmatter.get("决策人", "Founder Agent")}}
            properties["决策类型"] = {"select": {"name": doc.frontmatter.get("类型", "架构决策")}}
            properties["状态"] = {"select": {"name": "已通过"}}
        
        elif doc.doc_type == DocType.TECHNICAL:
            properties["类型"] = {"select": {"name": "技术文档"}}
            properties["优先级"] = {"select": {"name": "P3-正常"}}
            properties["状态"] = {"select": {"name": "已完成"}}
            properties["维护者"] = {"select": {"name": "CTO Agent"}}
        
        elif doc.doc_type == DocType.TASK:
            properties["状态"] = {"select": {"name": "待办"}}
            if doc.frontmatter.get("优先级"):
                properties["优先级"] = {"select": {"name": doc.frontmatter.get("优先级")}}
        
        # Obsidian 路径
        properties["Obsidian路径"] = {"url": f"file://{doc.relative_path}"}
        
        # 最后同步时间
        properties["最后同步"] = {"date": {"start": datetime.now().isoformat()}}
        
        # 标签
        properties["标签"] = {"multi_select": [{"name": "已同步"}]}
        
        return properties
    
    def _append_blocks(self, page_id: str, blocks: List[Dict]):
        """追加块到页面"""
        # Notion API 每次最多添加 100 个块
        for i in range(0, len(blocks), 100):
            chunk = blocks[i:i + 100]
            try:
                self.client.post(f"blocks/{page_id}/children", {"children": chunk})
            except Exception as e:
                print(f"⚠️  追加块失败: {e}")
    
    def sync_folder(self, folder: str) -> List[SyncResult]:
        """同步文件夹"""
        print(f"\n{'='*60}")
        print(f"📁 同步文件夹: {folder}")
        print(f"{'='*60}")
        
        # 扫描文件
        files = self.scan_folder(folder)
        print(f"找到 {len(files)} 个 Markdown 文件")
        
        results = []
        
        for file_path in files:
            # 解析文档
            doc = self.parse_document(file_path)
            if not doc:
                results.append(SyncResult(
                    success=False,
                    doc_path=file_path,
                    error="解析失败",
                    action="failed"
                ))
                continue
            
            # 获取对应的数据库
            database_id = self.get_database_id(doc.doc_type)
            
            if not database_id:
                print(f"⚠️  未找到数据库 {doc.doc_type.value}, 跳过: {doc.title}")
                results.append(SyncResult(
                    success=False,
                    doc_path=file_path,
                    error=f"未找到数据库: {doc.doc_type.value}",
                    action="skipped"
                ))
                continue
            
            # 创建页面
            print(f"  创建: {doc.title} ({doc.doc_type.value})")
            page_id = self.create_page(doc, database_id)
            
            if page_id:
                print(f"    ✅ 成功! ID: {page_id[:8]}...")
                results.append(SyncResult(
                    success=True,
                    doc_path=file_path,
                    notion_id=page_id,
                    action="created"
                ))
            else:
                print(f"    ❌ 失败")
                results.append(SyncResult(
                    success=False,
                    doc_path=file_path,
                    error="创建失败",
                    action="failed"
                ))
        
        self.sync_log.extend(results)
        return results
    
    def sync_all(self) -> List[SyncResult]:
        """同步所有配置的文件夹"""
        all_results = []
        
        for folder in OBSIDIAN_FOLDERS:
            folder_results = self.sync_folder(folder)
            all_results.extend(folder_results)
        
        return all_results
    
    def print_summary(self):
        """打印同步摘要"""
        total = len(self.sync_log)
        success = len([r for r in self.sync_log if r.success])
        failed = len([r for r in self.sync_log if not r.success])
        skipped = len([r for r in self.sync_log if r.action == "skipped"])
        
        print("\n" + "="*60)
        print("📊 同步结果摘要")
        print("="*60)
        print(f"  总计: {total}")
        print(f"  ✅ 成功: {success}")
        print(f"  ❌ 失败: {failed}")
        print(f"  ⏭️  跳过: {skipped}")
        print("="*60)
        
        # 按文档类型统计
        by_type = {}
        for r in self.sync_log:
            doc_type = os.path.dirname(r.doc_path).split(os.sep)[-1]
            by_type[doc_type] = by_type.get(doc_type, {"success": 0, "failed": 0})
            if r.success:
                by_type[doc_type]["success"] += 1
            else:
                by_type[doc_type]["failed"] += 1
        
        print("\n📁 按文件夹统计:")
        for folder, stats in by_type.items():
            print(f"  {folder}: ✅{stats['success']} ❌{stats['failed']}")

# ============================================================================
# 主函数
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Obsidian 到 Notion 同步")
    parser.add_argument("--folder", "-f", help="同步指定文件夹")
    parser.add_argument("--file", help="同步单个文件")
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
        print("将创建页面到根目录...")
    
    # 创建同步器
    sync = ObsidianToNotionSync(NOTION_TOKEN, db_config)
    
    if args.file:
        # 同步单个文件
        doc = sync.parse_document(args.file)
        if doc:
            database_id = sync.get_database_id(doc.doc_type)
            if database_id:
                page_id = sync.create_page(doc, database_id)
                if page_id:
                    print(f"✅ 创建成功: {page_id}")
                else:
                    print("❌ 创建失败")
            else:
                print(f"⚠️  未找到对应数据库: {doc.doc_type.value}")
    else:
        # 同步文件夹或所有
        folder = args.folder if args.folder else None
        
        if folder:
            sync.sync_folder(folder)
        else:
            sync.sync_all()
        
        sync.print_summary()

if __name__ == "__main__":
    main()
