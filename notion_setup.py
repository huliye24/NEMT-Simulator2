#!/usr/bin/env python3
"""
Notion 数据库设置脚本
==================

创建 NEMT 量化系统所需的 Notion 数据库:
1. DesignSchemes - 设计方案数据库
2. Milestones - 里程碑数据库
3. IterationLogs - 迭代日志数据库

使用方法:
    python setup_notion_databases.py

注意: 运行前请确保设置了 NOTION_TOKEN 环境变量
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

# 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "ntn_s640536110656ijG4LStAQzrntOjxNtIhVajRcYSh68eWt")
PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "")  # 可选，数据库将创建在此页面下

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
        req = urllib.request.Request(
            url, data=request_data, headers=HEADERS, method="PATCH"
        )
    elif method == "DELETE":
        req = urllib.request.Request(url, headers=HEADERS, method="DELETE")
    else:
        req = urllib.request.Request(
            url, data=request_data, headers=HEADERS
        )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ HTTP Error {e.code}: {error_body}")
        raise


def create_database(name: str, properties: dict, parent_page_id: str = None) -> dict:
    """创建数据库"""
    parent = {"page_id": parent_page_id} if parent_page_id else {"database_id": PARENT_PAGE_ID}

    data = {
        "parent": parent,
        "title": [{"type": "text", "text": {"content": name}}],
        "properties": properties
    }

    return make_request("databases", data)


def create_page(parent_id: str, properties: dict) -> dict:
    """创建页面"""
    data = {
        "parent": {"page_id": parent_id} if len(parent_id) > 30 else {"database_id": parent_id},
        "properties": properties
    }
    return make_request("pages", data)


# ============================================================================
# 数据库Schema定义
# ============================================================================

DESIGN_SCHEMES_SCHEMA = {
    "方案名称": {"title": {}},
    "状态": {
        "select": {
            "options": [
                {"name": "📝 草案", "color": "gray"},
                {"name": "🟡 待审阅", "color": "yellow"},
                {"name": "✅ 已批准", "color": "green"},
                {"name": "❌ 已拒绝", "color": "red"},
                {"name": "🚧 进行中", "color": "blue"},
                {"name": "🏁 已完成", "color": "purple"}
            ]
        }
    },
    "创建时间": {"date": {}},
    "审阅人": {"rich_text": {}},
    "背景": {"rich_text": {}},
    "设计决策": {"rich_text": {}},
    "影响模块": {
        "multi_select": {
            "options": [
                {"name": "MarketLayer", "color": "blue"},
                {"name": "NEMTCore", "color": "green"},
                {"name": "SignalLayer", "color": "yellow"},
                {"name": "RiskLayer", "color": "red"},
                {"name": "OnChainLayer", "color": "purple"},
                {"name": "PhaseStateMachine", "color": "orange"},
                {"name": "ExecutionLayer", "color": "pink"},
                {"name": "BrainLayer", "color": "brown"},
                {"name": "EvolutionLayer", "color": "gray"},
                {"name": "API Server", "color": "default"},
                {"name": "Web Frontend", "color": "default"}
            ]
        }
    },
    "接口变更": {"rich_text": {}},
    "验收标准": {"rich_text": {}},
    "预估工时": {"number": {"format": "number"}},
    "实际工时": {"number": {"format": "number"}},
    "详细说明": {"rich_text": {}}
}

MILESTONES_SCHEMA = {
    "名称": {"title": {}},
    "状态": {
        "select": {
            "options": [
                {"name": "🔴 已阻塞", "color": "red"},
                {"name": "📋 待开始", "color": "gray"},
                {"name": "🚧 进行中", "color": "blue"},
                {"name": "🟡 等待中", "color": "yellow"},
                {"name": "✅ 已完成", "color": "green"}
            ]
        }
    },
    "版本": {"select": {"options": [
        {"name": "v0.1"}, {"name": "v0.2"}, {"name": "v0.3"}, {"name": "v1.0"}
    ]}},
    "开始日期": {"date": {}},
    "结束日期": {"date": {}},
    "进度": {"number": {"format": "percent"}},
    "优先级": {
        "select": {"options": [
            {"name": "P0 - 必须"}, {"name": "P1 - 重要"}, {"name": "P2 - 优化"}
        ]}
    },
    "预估天数": {"number": {"format": "number"}},
    "实际天数": {"number": {"format": "number"}},
    "依赖": {"relation": {"database_id": "", "single_property": {}}},
    "前置任务": {"relation": {"database_id": "", "single_property": {}}},
    "负责人": {"rich_text": {}},
    "备注": {"rich_text": {}}
}

ITERATION_LOGS_SCHEMA = {
    "周期名称": {"title": {}},
    "状态": {
        "select": {
            "options": [
                {"name": "🏃 进行中", "color": "blue"},
                {"name": "✅ 已完成", "color": "green"},
                {"name": "⏸️ 暂停", "color": "yellow"}
            ]
        }
    },
    "开始时间": {"date": {}},
    "结束时间": {"date": {}},
    "里程碑": {"relation": {"database_id": "", "single_property": {}}},
    "实际产出": {"rich_text": {}},
    "遇到的问题": {"rich_text": {}},
    "下一周期起点": {"rich_text": {}},
    "休息计划": {"rich_text": {}}
}

DEBUG_RECORDS_SCHEMA = {
    "调试编号": {"title": {}},
    "日期": {"date": {}},
    "问题描述": {"rich_text": {}},
    "定位方法": {"rich_text": {}},
    "根本原因": {"rich_text": {}},
    "修复方案": {"rich_text": {}},
    "涉及模块": {
        "multi_select": {
            "options": [
                {"name": "MarketLayer"}, {"name": "NEMTCore"},
                {"name": "SignalLayer"}, {"name": "RiskLayer"},
                {"name": "ExecutionLayer"}, {"name": "API Server"},
                {"name": "Web Frontend"}
            ]
        }
    },
    "验证结果": {"select": {"options": [
        {"name": "✅ 通过"}, {"name": "❌ 未通过"}
    ]}},
    "新增测试用例": {"checkbox": {}}
}


def main():
    print("=" * 60)
    print("NEMT Notion 数据库设置")
    print("=" * 60)
    print()

    created_databases = []

    # 1. 创建 DesignSchemes 数据库
    print("📦 创建 DesignSchemes 数据库...")
    try:
        result = create_database("DesignSchemes", DESIGN_SCHEMES_SCHEMA, PARENT_PAGE_ID)
        db_id = result.get("id", "")
        created_databases.append({
            "name": "DesignSchemes",
            "id": db_id,
            "url": f"https://notion.so/{db_id.replace('-', '')}"
        })
        print(f"✅ DesignSchemes 创建成功: {db_id}")
    except Exception as e:
        print(f"⚠️  DesignSchemes 创建失败: {e}")

    # 2. 创建 Milestones 数据库
    print("\n📦 创建 Milestones 数据库...")
    try:
        result = create_database("Milestones", MILESTONES_SCHEMA, PARENT_PAGE_ID)
        db_id = result.get("id", "")
        created_databases.append({
            "name": "Milestones",
            "id": db_id,
            "url": f"https://notion.so/{db_id.replace('-', '')}"
        })
        print(f"✅ Milestones 创建成功: {db_id}")
    except Exception as e:
        print(f"⚠️  Milestones 创建失败: {e}")

    # 3. 创建 IterationLogs 数据库
    print("\n📦 创建 IterationLogs 数据库...")
    try:
        result = create_database("IterationLogs", ITERATION_LOGS_SCHEMA, PARENT_PAGE_ID)
        db_id = result.get("id", "")
        created_databases.append({
            "name": "IterationLogs",
            "id": db_id,
            "url": f"https://notion.so/{db_id.replace('-', '')}"
        })
        print(f"✅ IterationLogs 创建成功: {db_id}")
    except Exception as e:
        print(f"⚠️  IterationLogs 创建失败: {e}")

    # 4. 创建 DebugRecords 数据库
    print("\n📦 创建 DebugRecords 数据库...")
    try:
        result = create_database("DebugRecords", DEBUG_RECORDS_SCHEMA, PARENT_PAGE_ID)
        db_id = result.get("id", "")
        created_databases.append({
            "name": "DebugRecords",
            "id": db_id,
            "url": f"https://notion.so/{db_id.replace('-', '')}"
        })
        print(f"✅ DebugRecords 创建成功: {db_id}")
    except Exception as e:
        print(f"⚠️  DebugRecords 创建失败: {e}")

    # 输出总结
    print("\n" + "=" * 60)
    print("创建完成!")
    print("=" * 60)

    if created_databases:
        print("\n已创建的数据库:")
        for db in created_databases:
            print(f"  • {db['name']}: {db['id']}")

        # 保存到文件
        config = {
            "created_at": datetime.now().isoformat(),
            "databases": created_databases
        }
        with open("notion_databases_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"\n💾 配置已保存到: notion_databases_config.json")
    else:
        print("\n❌ 没有数据库被创建，请检查错误信息")


if __name__ == "__main__":
    main()
