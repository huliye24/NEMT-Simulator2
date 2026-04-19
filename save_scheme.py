#!/usr/bin/env python3
"""
保存设计方案到 Notion
====================

接收 Cursor 输出的 JSON 方案并写入 Notion DesignSchemes 数据库。

使用方法:
    python save_scheme.py '{"scheme_name": "...", "background": "...", ...}'
    # 或
    python save_scheme.py --file scheme.json

示例:
    python save_scheme.py "{\"scheme_name\": \"BrainLayer实现\", \"background\": \"需要完善大脑层\"}"
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional

# 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "ntn_s640536110656ijG4LStAQzrntOjxNtIhVajRcYSh68eWt")
DATABASE_ID = os.getenv("NOTION_SCHEMES_DB", "")  # 从 setup_notion_databases.py 获取

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

BASE_URL = "https://api.notion.com/v1"


def make_request(endpoint: str, data: dict = None, method: str = None) -> dict:
    """发送 Notion API 请求"""
    url = f"{BASE_URL}/{endpoint}"
    request_data = json.dumps(data).encode() if data else None

    if method == "PATCH":
        req = urllib.request.Request(url, data=request_data, headers=HEADERS, method="PATCH")
    elif method == "DELETE":
        req = urllib.request.Request(url, headers=HEADERS, method="DELETE")
    else:
        req = urllib.request.Request(url, data=request_data, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"HTTP Error {e.code}: {error_body}")


def load_scheme_from_file(filepath: str) -> Dict[str, Any]:
    """从文件加载方案数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_scheme(scheme_data: Dict[str, Any], database_id: str = None) -> Optional[str]:
    """
    保存设计方案到 Notion

    Args:
        scheme_data: 方案数据，包含:
            - scheme_name: 方案名称
            - background: 背景与问题陈述
            - design_decisions: 设计决策列表
            - affected_modules: 影响模块列表
            - interface_changes: 接口变更
            - acceptance_criteria: 验收标准列表
            - estimated_hours: 预估工时
            - markdown_explanation: 详细说明
            - reviewer: 审阅人 (可选)

    Returns:
        创建的页面ID，失败返回None
    """
    db_id = database_id or DATABASE_ID
    if not db_id:
        print("❌ 错误: 未设置 DATABASE_ID")
        print("   请设置 NOTION_SCHEMES_DB 环境变量或传入 database_id 参数")
        return None

    # 构建 Notion 属性
    properties = {
        "方案名称": {
            "title": [{"text": {"content": scheme_data.get("scheme_name", "未命名方案")}}]
        },
        "状态": {
            "select": {"name": "📝 草案"}
        },
        "创建时间": {
            "date": {"start": datetime.now().isoformat()}
        },
        "审阅人": {
            "rich_text": [{"text": {"content": scheme_data.get("reviewer", "待指定")}}]
        },
        "背景": {
            "rich_text": [{"text": {"content": scheme_data.get("background", "")}}]
        },
        "设计决策": {
            "rich_text": [{"text": {"content": "\n".join(scheme_data.get("design_decisions", []))}}]
        },
        "影响模块": {
            "multi_select": [{"name": m} for m in scheme_data.get("affected_modules", [])]
        },
        "接口变更": {
            "rich_text": [{"text": {"content": scheme_data.get("interface_changes", "")}}]
        },
        "验收标准": {
            "rich_text": [{"text": {"content": "\n".join(scheme_data.get("acceptance_criteria", []))}}]
        },
        "预估工时": {
            "number": scheme_data.get("estimated_hours", 0)
        },
        "详细说明": {
            "rich_text": [{"text": {"content": scheme_data.get("markdown_explanation", "")}}]
        }
    }

    # 发送到 Notion
    try:
        result = make_request("pages", {
            "parent": {"database_id": db_id},
            "properties": properties
        })
        page_id = result.get("id", "")
        print(f"✅ 方案已存入 Notion: {page_id}")
        print(f"   链接: https://notion.so/{page_id.replace('-', '')}")
        return page_id
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None


def list_schemes(database_id: str = None, status_filter: str = None) -> list:
    """
    列出 Notion 中的设计方案

    Args:
        database_id: 数据库ID
        status_filter: 按状态筛选 (如 "已批准", "进行中")

    Returns:
        方案列表
    """
    db_id = database_id or DATABASE_ID
    if not db_id:
        print("❌ 错误: 未设置 DATABASE_ID")
        return []

    # 构建筛选条件
    filter_data = None
    if status_filter:
        filter_data = {
            "property": "状态",
            "select": {"equals": status_filter}
        }

    try:
        result = make_request(f"databases/{db_id}/query", {
            "filter": filter_data,
            "sorts": [{"timestamp": "created_time", "direction": "descending"}]
        })

        schemes = []
        for page in result.get("results", []):
            props = page.get("properties", {})

            # 提取标题
            title = ""
            if "方案名称" in props and props["方案名称"].get("title"):
                title = "".join([t.get("plain_text", "") for t in props["方案名称"]["title"]])

            # 提取状态
            status = ""
            if "状态" in props and props["状态"].get("select"):
                status = props["状态"]["select"].get("name", "")

            # 提取预估工时
            hours = 0
            if "预估工时" in props and props["预估工时"].get("number"):
                hours = props["预估工时"]["number"]

            schemes.append({
                "id": page.get("id", ""),
                "name": title,
                "status": status,
                "estimated_hours": hours,
                "created_time": page.get("created_time", "")
            })

        return schemes

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return []


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("保存设计方案到 Notion")
        print("=" * 60)
        print("\n使用方法:")
        print("  python save_scheme.py '<JSON数据>'")
        print("  python save_scheme.py --file <文件路径>")
        print("  python save_scheme.py --list [状态筛选]")
        print("\nJSON 格式:")
        print("""
{
  "scheme_name": "方案名称",
  "background": "背景与问题陈述",
  "design_decisions": ["决策1", "决策2"],
  "affected_modules": ["NEMTCore", "RiskLayer"],
  "interface_changes": "接口变更说明",
  "acceptance_criteria": ["标准1", "标准2"],
  "estimated_hours": 8,
  "markdown_explanation": "详细说明"
}
""")
        print(f"\n当前 DATABASE_ID: {DATABASE_ID or '(未设置)'}")
        return

    # 列出方案
    if sys.argv[1] == "--list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        schemes = list_schemes(status_filter=status)

        print(f"\n{'='*60}")
        print(f"设计方案列表 (共 {len(schemes)} 个)")
        print(f"{'='*60}")

        for s in schemes:
            print(f"\n• {s['name']}")
            print(f"  状态: {s['status']}")
            print(f"  预估: {s['estimated_hours']}小时")
            print(f"  创建: {s['created_time'][:10]}")
            print(f"  ID: {s['id']}")

        return

    # 从文件加载
    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("❌ 请提供文件路径")
            return
        try:
            scheme_data = load_scheme_from_file(sys.argv[2])
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
    else:
        # 解析 JSON
        try:
            scheme_data = json.loads(sys.argv[1])
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return

    # 验证必需字段
    required = ["scheme_name", "background"]
    missing = [f for f in required if f not in scheme_data]
    if missing:
        print(f"⚠️  缺少字段: {', '.join(missing)}")
        print("   将使用默认值继续...")

    # 保存
    save_scheme(scheme_data)


if __name__ == "__main__":
    main()
