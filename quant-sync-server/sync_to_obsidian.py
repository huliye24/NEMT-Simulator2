#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian MCP Server - 同步脚本
=============================
将项目信息同步到 Obsidian Vault

使用前:
1. 安装 Obsidian Local REST API 插件
2. 启用插件并获取 API Key
3. 配置 OBSIDIAN_API_KEY 环境变量
4. 运行: python sync_to_obsidian.py

依赖:
    pip install requests
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Any

# Fix encoding - 必须在任何 I/O 之前
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============ 配置 ============

def load_env():
    """从 .env 文件加载配置"""
    env_path = os.path.join(os.path.dirname(__file__), 'obsidian.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

OBSIDIAN_API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")
OBSIDIAN_HOST = os.environ.get("OBSIDIAN_HOST", "127.0.0.1")
OBSIDIAN_PORT = os.environ.get("OBSIDIAN_PORT", "27124")
VAULT_NAME = os.environ.get("OBSIDIAN_VAULT", "NEMT-Simulator")

BASE_URL = f"https://{OBSIDIAN_HOST}:{OBSIDIAN_PORT}"


def log(msg):
    """安全的日志输出"""
    try:
        print(msg)
    except:
        pass


def get_headers():
    return {
        'Authorization': f'Bearer {OBSIDIAN_API_KEY}',
        'Content-Type': 'application/json',
    }


def check_connection() -> bool:
    """检查 Obsidian API 连接"""
    try:
        response = requests.get(
            f"{BASE_URL}/vault/",
            headers=get_headers(),
            verify=False,
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        log(f"[FAIL] Cannot connect: {e}")
        return False


def create_note(folder: str, filename: str, content: str) -> bool:
    """创建或更新笔记"""
    path = f"{folder}/{filename}.md" if folder else f"{filename}.md"
    try:
        response = requests.put(
            f"{BASE_URL}/vault/{path}",
            headers={'Authorization': f'Bearer {OBSIDIAN_API_KEY}'},
            data=content.encode('utf-8'),
            verify=False
        )
        success = response.status_code in [200, 201]
        status = "[OK]" if success else "[FAIL]"
        log(f"  {status} {path} ({response.status_code})")
        return success
    except Exception as e:
        log(f"  [ERROR] {path}: {e}")
        return False


def create_folder(folder: str) -> bool:
    """创建文件夹"""
    try:
        requests.post(
            f"{BASE_URL}/vault/{folder}/",
            headers={'Authorization': f'Bearer {OBSIDIAN_API_KEY}'},
            verify=False
        )
        return True
    except:
        return True


def extract_property(prop: Dict) -> Any:
    """提取 Notion 属性值"""
    prop_type = prop.get('type', '')
    if prop_type == 'title':
        return ''.join(t.get('text', {}).get('content', '') for t in prop.get('title', []))
    elif prop_type == 'rich_text':
        return ''.join(t.get('text', {}).get('content', '') for t in prop.get('rich_text', []))
    elif prop_type == 'number':
        return prop.get('number')
    elif prop_type == 'checkbox':
        return prop.get('checkbox')
    elif prop_type == 'select':
        s = prop.get('select')
        return s.get('name') if s else None
    elif prop_type == 'multi_select':
        return [m.get('name') for m in prop.get('multi_select', [])]
    elif prop_type == 'date':
        d = prop.get('date')
        return d.get('start') if d else None
    return None


def extract_props(item: Dict) -> Dict:
    """提取所有属性"""
    return {k: extract_property(v) for k, v in item.get('properties', {}).items()}


# ============ 笔记生成 ============

def generate_index_note() -> str:
    return f"""# NEMT Quant OS - 项目总览

> **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> **项目状态**: 开发中

---

## 项目架构

```
NEMT Quant OS
├── Web UI (React)
├── Python Core
│   ├── NEMT Engine
│   ├── Signal Generator
│   ├── Risk Manager
│   └── quant-sync-server
└── Notion 知识库
```

## 核心模块

- [[TechTree/科技树]] - 技术升级路径追踪
- [[WorkLog/工作日志]] - 开发进度记录
- [[NodeTasks/节点任务]] - 核心Node开发
- [[DesignSchemes/设计方案]] - 设计方案管理

## 开发阶段

- [x] Phase 1: 厨房阶段 - 架构搭建
- [x] Phase 2: 厨房阶段 - 数据层
- [ ] Phase 3: 厨师阶段 - NEMT Core
- [ ] Phase 4: 厨师阶段 - 策略层
- [ ] Phase 5: 厨师阶段 - 风控/大脑层
- [ ] Phase 6: 生产化
"""


def generate_techtree_note(items: List[Dict]) -> str:
    completed = [i for i in items if i.get('状态') == '已完成']
    not_started = [i for i in items if i.get('状态') == '未开始']
    
    def format_item(item):
        name = item.get('科技节点', '')
        dim = item.get('维度', '')
        level = item.get('当前等级', '')
        effect = item.get('效果指标', '')
        return f"""### {name}

- **维度**: {dim}
- **等级**: {level}
- **效果**: {effect}

"""
    
    completed_md = '\n'.join(format_item(i) for i in completed) if completed else "_暂无_"
    not_started_md = '\n'.join(format_item(i) for i in not_started) if not_started else "_暂无_"
    
    return f"""# TechTree - 技术树

> **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 已完成

{completed_md}

## 未开始

{not_started_md}
"""


def generate_worklog_note(items: List[Dict]) -> str:
    logs = []
    for item in items:
        name = item.get('阶段名称', '')
        completed = item.get('完成时间', '')
        hours = item.get('耗时(小时)', 0)
        metrics = item.get('关键指标', '')
        next_steps = item.get('下一步计划', '')
        verified = item.get('验收通过', False)
        
        status = "OK" if verified else "PENDING"
        
        logs.append(f"""## {status} {name}

- **时间**: {completed}
- **耗时**: {hours}h
- **指标**: {metrics}
- **下一步**: {next_steps}

""")
    
    return f"""# WorkLog - 工作日志

> **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{"".join(logs) if logs else "_暂无记录_"}
"""


def generate_nodetask_note(items: List[Dict]) -> str:
    by_type = {}
    for item in items:
        node_type = item.get('类型', 'Other')
        by_type.setdefault(node_type, []).append(item)
    
    content = f"""# NodeTasks - 节点任务

> **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> **总计**: {len(items)} 个 Node

---

"""
    
    for node_type, node_list in sorted(by_type.items()):
        content += f"## {node_type}\n\n"
        for item in node_list:
            name = item.get('Node名称', '')
            coverage = item.get('测试覆盖', 0)
            output = item.get('实际产出', '')
            content += f"- **{name}** (测试: {coverage}%) - {output}\n"
        content += "\n"
    
    # Summary table
    content += "---\n\n## 概览表\n\n"
    content += "| Node | 类型 | 测试覆盖 |\n"
    content += "|------|------|----------|\n"
    for item in items:
        name = item.get('Node名称', '')
        node_type = item.get('类型', '')
        coverage = item.get('测试覆盖', 0)
        content += f"| {name} | {node_type} | {coverage}% |\n"
    
    return content


def generate_design_schemes_note(items: List[Dict]) -> str:
    pending = [i for i in items if i.get('状态') in ['草案', '待审阅']]
    completed = [i for i in items if i.get('状态') == '已完成']
    
    pending_md = ""
    for item in pending:
        name = item.get('方案名称', '')
        status = item.get('状态', '')
        hours = item.get('预估工时', 0)
        modules = item.get('影响模块', [])
        background = item.get('背景', '')
        criteria = item.get('验收标准', '')
        pending_md += f"""### {name}

- **状态**: {status}
- **工时**: {hours}h
- **影响**: {', '.join(modules) if isinstance(modules, list) else modules}
- **背景**: {background}
- **验收**: {criteria}

"""
    
    completed_md = '\n'.join(f"- [OK] {i.get('方案名称', '')}" for i in completed) if completed else "_暂无_"
    
    content = f"""# DesignSchemes - 设计方案

> **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 待处理

{pending_md if pending_md else "_暂无待处理方案_"}

## 已完成

{completed_md}

---

## 全部方案

| 方案 | 状态 | 工时 |
|------|------|------|
"""
    
    for item in items:
        name = item.get('方案名称', '')
        status = item.get('状态', '')
        hours = item.get('预估工时', 0)
        content += f"| {name} | {status} | {hours}h |\n"
    
    return content


# ============ 主函数 ============

def main():
    print("=" * 60)
    print("NEMT Simulator - Obsidian Sync")
    print("=" * 60)
    print()
    
    if not OBSIDIAN_API_KEY or OBSIDIAN_API_KEY == "your-obsidian-api-key-here":
        print("[ERROR] OBSIDIAN_API_KEY not configured!")
        print()
        print("配置方法:")
        print("1. 打开 Obsidian")
        print("2. 设置 -> Local REST API")
        print("3. 复制 API Key")
        print("4. 编辑 obsidian.env 文件")
        return
    
    print(f"[INFO] Target: {VAULT_NAME}")
    
    if not check_connection():
        return
    
    # 导入 Notion 获取数据
    sys.path.insert(0, os.path.dirname(__file__))
    
    techtree = worklog = node = design = []
    
    try:
        from fetch_notion_pages import (
            load_token as load_notion_token,
            get_headers as get_notion_headers,
            query_database
        )
        
        NOTION_TOKEN = load_notion_token()
        if NOTION_TOKEN:
            notion_headers = get_notion_headers(NOTION_TOKEN)
            
            # Database IDs
            databases = {
                'techtree': "f5620ee6-b4e6-47f9-8420-f223cd6d808b",
                'worklog': "de72f83c-b3c8-4b88-804e-92ce9cb738a2",
                'node': "d679b710-2e5c-4714-a793-3fe260e6db37",
                'design': "b84a2950-142c-49b8-9c5a-9ef876dbd933",
            }
            
            print("\n[INFO] Fetching Notion data...")
            
            for name, db_id in databases.items():
                results, _ = query_database(db_id, notion_headers, max_items=20)
                if name == 'techtree':
                    techtree = [extract_props(r) for r in results]
                elif name == 'worklog':
                    worklog = [extract_props(r) for r in results]
                elif name == 'node':
                    node = [extract_props(r) for r in results]
                elif name == 'design':
                    design = [extract_props(r) for r in results]
            
        else:
            print("[WARN] Notion token not found, using sample data")
            
    except Exception as e:
        print(f"[WARN] Failed to fetch Notion data: {e}")
        print("[INFO] Will sync with existing data")
    
    # 创建文件夹
    print("\n[INFO] Creating folders...")
    for folder in ['TechTree', 'WorkLog', 'NodeTasks', 'DesignSchemes']:
        create_folder(folder)
    
    # 生成笔记
    print("\n[INFO] Generating notes...")
    create_note("", "00-项目总览", generate_index_note())
    create_note("TechTree", "科技树", generate_techtree_note(techtree))
    create_note("WorkLog", "工作日志", generate_worklog_note(worklog))
    create_note("NodeTasks", "节点任务", generate_nodetask_note(node))
    create_note("DesignSchemes", "设计方案", generate_design_schemes_note(design))
    
    print()
    print("=" * 60)
    print("Sync Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
