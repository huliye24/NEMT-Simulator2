#!/usr/bin/env python3
"""
迭代日志与里程碑跟踪脚本
========================

用于记录和管理迭代开发周期、里程碑状态。

使用方法:
    # 记录新周期
    python iteration_tracker.py new "周期名称"

    # 完成当前周期
    python iteration_tracker.py complete --output "完成了xxx" --problems "遇到xxx问题"

    # 更新里程碑
    python iteration_tracker.py milestone --name "v0.2" --status "进行中" --progress 50

    # 查看状态
    python iteration_tracker.py status
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# 配置
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "ntn_s640536110656ijG4LStAQzrntOjxNtIhVajRcYSh68eWt")
ITERATION_DB = os.getenv("NOTION_ITERATION_DB", "")
MILESTONE_DB = os.getenv("NOTION_MILESTONE_DB", "")

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


# ============================================================================
# 迭代周期管理
# ============================================================================

def start_iteration(name: str, milestone_id: str = None) -> Optional[str]:
    """开始新迭代周期"""
    if not ITERATION_DB:
        print("⚠️  未配置 NOTION_ITERATION_DB，将使用本地记录")
        return save_local_iteration({
            "name": name,
            "start_time": datetime.now().isoformat(),
            "status": "进行中",
            "milestone_id": milestone_id,
            "outputs": [],
            "problems": [],
            "next_start": ""
        })

    properties = {
        "周期名称": {"title": [{"text": {"content": name}}]},
        "状态": {"select": {"name": "🏃 进行中"}},
        "开始时间": {"date": {"start": datetime.now().isoformat()}},
    }

    if milestone_id:
        properties["里程碑"] = {"relation": [{"id": milestone_id}]}

    result = make_request("pages", {
        "parent": {"database_id": ITERATION_DB},
        "properties": properties
    })

    page_id = result.get("id", "")
    print(f"✅ 新迭代周期开始: {name}")
    print(f"   页面ID: {page_id}")
    return page_id


def complete_iteration(
    page_id: str = None,
    outputs: str = "",
    problems: str = "",
    next_start: str = ""
) -> bool:
    """完成当前迭代周期"""
    if not page_id:
        print("❌ 请提供页面ID (--page-id)")
        return False

    if not ITERATION_DB:
        # 本地模式
        iterations = load_local_iterations()
        if iterations:
            it = iterations[-1]
            it["status"] = "已完成"
            it["end_time"] = datetime.now().isoformat()
            it["outputs"] = outputs.split("\n") if outputs else []
            it["problems"] = problems.split("\n") if problems else []
            it["next_start"] = next_start
            save_local_iterations(iterations)
        return True

    # Notion 模式
    properties = {
        "状态": {"select": {"name": "✅ 已完成"}},
        "结束时间": {"date": {"start": datetime.now().isoformat()}},
    }

    if outputs:
        properties["实际产出"] = {"rich_text": [{"text": {"content": outputs}}]}
    if problems:
        properties["遇到的问题"] = {"rich_text": [{"text": {"content": problems}}]}
    if next_start:
        properties["下一周期起点"] = {"rich_text": [{"text": {"content": next_start}}]}

    make_request(f"pages/{page_id}", {"properties": properties}, method="PATCH")
    print(f"✅ 迭代周期已完成: {page_id}")
    return True


def get_current_iteration() -> Optional[Dict]:
    """获取当前进行中的迭代"""
    if not ITERATION_DB:
        iterations = load_local_iterations()
        for it in reversed(iterations):
            if it.get("status") == "进行中":
                return it
        return None

    try:
        result = make_request(f"databases/{ITERATION_DB}/query", {
            "filter": {
                "property": "状态",
                "select": {"equals": "🏃 进行中"}
            },
            "page_size": 1
        })

        pages = result.get("results", [])
        if pages:
            return parse_iteration_page(pages[0])
    except Exception as e:
        print(f"⚠️  查询失败: {e}")

    return None


# ============================================================================
# 里程碑管理
# ============================================================================

def create_milestone(
    name: str,
    version: str = "v0.1",
    start_date: str = None,
    end_date: str = None,
    estimated_days: int = 5,
    priority: str = "P1 - 重要"
) -> Optional[str]:
    """创建新里程碑"""
    if not MILESTONE_DB:
        print("⚠️  未配置 NOTION_MILESTONE_DB，将使用本地记录")
        return save_local_milestone({
            "name": name,
            "version": version,
            "start_date": start_date or datetime.now().strftime("%Y-%m-%d"),
            "end_date": end_date or (datetime.now() + timedelta(days=estimated_days)).strftime("%Y-%m-%d"),
            "status": "待开始",
            "progress": 0,
            "estimated_days": estimated_days,
            "actual_days": 0,
            "priority": priority,
            "tasks": []
        })

    properties = {
        "名称": {"title": [{"text": {"content": name}}]},
        "状态": {"select": {"name": "📋 待开始"}},
        "版本": {"select": {"name": version}},
        "优先级": {"select": {"name": priority}},
        "预估天数": {"number": estimated_days},
        "进度": {"number": 0}
    }

    if start_date:
        properties["开始日期"] = {"date": {"start": start_date}}
    if end_date:
        properties["结束日期"] = {"date": {"start": end_date}}

    result = make_request("pages", {
        "parent": {"database_id": MILESTONE_DB},
        "properties": properties
    })

    page_id = result.get("id", "")
    print(f"✅ 里程碑已创建: {name}")
    print(f"   版本: {version}")
    print(f"   页面ID: {page_id}")
    return page_id


def update_milestone_progress(page_id: str, progress: int, notes: str = None) -> bool:
    """更新里程碑进度"""
    if not MILESTONE_DB:
        milestones = load_local_milestones()
        for m in milestones:
            if m.get("id") == page_id or m.get("name") == page_id:
                m["progress"] = progress
                save_local_milestones(milestones)
                print(f"✅ 里程碑进度已更新: {m['name']} -> {progress}%")
                return True
        return False

    properties = {
        "进度": {"number": progress / 100.0}
    }

    if notes:
        properties["备注"] = {"rich_text": [{"text": {"content": notes}}]}

    # 如果进度100%，自动标记为完成
    if progress >= 100:
        properties["状态"] = {"select": {"name": "✅ 已完成"}}

    make_request(f"pages/{page_id}", {"properties": properties}, method="PATCH")
    print(f"✅ 里程碑进度已更新: {page_id} -> {progress}%")
    return True


def get_all_milestones() -> List[Dict]:
    """获取所有里程碑"""
    if not MILESTONE_DB:
        return load_local_milestones()

    try:
        result = make_request(f"databases/{MILESTONE_DB}/query", {
            "sorts": [{"property": "名称", "direction": "ascending"}]
        })

        milestones = []
        for page in result.get("results", []):
            milestones.append(parse_milestone_page(page))
        return milestones
    except Exception as e:
        print(f"⚠️  查询失败: {e}")
        return []


# ============================================================================
# 本地存储 (当Notion未配置时使用)
# ============================================================================

LOCAL_DATA_FILE = "iteration_data.json"


def load_local_data() -> Dict:
    """加载本地数据"""
    if os.path.exists(LOCAL_DATA_FILE):
        with open(LOCAL_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"iterations": [], "milestones": []}


def save_local_data(data: Dict) -> None:
    """保存本地数据"""
    with open(LOCAL_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_local_iteration(iteration: Dict) -> str:
    """保存本地迭代"""
    data = load_local_data()
    if not iteration.get("id"):
        iteration["id"] = f"local_{len(data['iterations']) + 1}"
    data["iterations"].append(iteration)
    save_local_data(data)
    return iteration["id"]


def load_local_iterations() -> List[Dict]:
    """加载本地迭代列表"""
    return load_local_data().get("iterations", [])


def save_local_milestone(milestone: Dict) -> str:
    """保存本地里程碑"""
    data = load_local_data()
    if not milestone.get("id"):
        milestone["id"] = f"local_m{len(data['milestones']) + 1}"
    data["milestones"].append(milestone)
    save_local_data(data)
    return milestone["id"]


def load_local_milestones() -> List[Dict]:
    """加载本地里程碑列表"""
    return load_local_data().get("milestones", [])


# ============================================================================
# 辅助函数
# ============================================================================

def parse_iteration_page(page: Dict) -> Dict:
    """解析迭代页面"""
    props = page.get("properties", {})

    return {
        "id": page.get("id"),
        "name": extract_title(props.get("周期名称")),
        "status": extract_select(props.get("状态")),
        "start_time": extract_date(props.get("开始时间")),
        "end_time": extract_date(props.get("结束时间")),
        "outputs": extract_text(props.get("实际产出")),
        "problems": extract_text(props.get("遇到的问题")),
        "next_start": extract_text(props.get("下一周期起点"))
    }


def parse_milestone_page(page: Dict) -> Dict:
    """解析里程碑页面"""
    props = page.get("properties", {})

    return {
        "id": page.get("id"),
        "name": extract_title(props.get("名称")),
        "status": extract_select(props.get("状态")),
        "version": extract_select(props.get("版本")),
        "start_date": extract_date(props.get("开始日期")),
        "end_date": extract_date(props.get("结束日期")),
        "progress": int(props.get("进度", {}).get("number", 0) * 100) if props.get("进度") else 0,
        "priority": extract_select(props.get("优先级")),
        "estimated_days": props.get("预估天数", {}).get("number", 0),
        "notes": extract_text(props.get("备注"))
    }


def extract_title(prop: Dict) -> str:
    if prop and prop.get("title"):
        return "".join([t.get("plain_text", "") for t in prop["title"]])
    return ""


def extract_select(prop: Dict) -> str:
    if prop and prop.get("select"):
        return prop["select"].get("name", "")
    return ""


def extract_date(prop: Dict) -> str:
    if prop and prop.get("date"):
        return prop["date"].get("start", "")
    return ""


def extract_text(prop: Dict) -> str:
    if prop and prop.get("rich_text"):
        return "".join([t.get("plain_text", "") for t in prop["rich_text"]])
    return ""


# ============================================================================
# CLI 命令
# ============================================================================

def cmd_status():
    """显示当前状态"""
    print("\n" + "=" * 60)
    print("NEMT 迭代开发状态")
    print("=" * 60)

    # 当前迭代
    current = get_current_iteration()
    if current:
        print(f"\n📍 当前迭代: {current.get('name', 'N/A')}")
        print(f"   状态: {current.get('status', 'N/A')}")
        start = current.get('start_time', '')[:10] if current.get('start_time') else 'N/A'
        print(f"   开始: {start}")
    else:
        print("\n📍 当前迭代: 无")

    # 里程碑
    milestones = get_all_milestones()
    print(f"\n📊 里程碑 ({len(milestones)} 个):")

    status_map = {
        "🔴 已阻塞": [],
        "📋 待开始": [],
        "🚧 进行中": [],
        "🟡 等待中": [],
        "✅ 已完成": []
    }

    for m in milestones:
        status = m.get("status", "📋 待开始")
        if status not in status_map:
            status_map[status] = []
        status_map[status].append(m)

    for status, items in status_map.items():
        if items:
            print(f"\n   {status}:")
            for m in items:
                progress = m.get("progress", 0)
                print(f"   • {m.get('name', 'N/A')} [{progress}%]")

    print("\n" + "=" * 60)


def cmd_new(args):
    """开始新迭代"""
    name = args[0] if args else f"迭代 {datetime.now().strftime('%Y%m%d')}"
    milestone_id = os.getenv("CURRENT_MILESTONE_ID", None)
    page_id = start_iteration(name, milestone_id)
    if page_id:
        print(f"\n💡 下次更新时设置: CURRENT_MILESTONE_PAGE_ID={page_id}")


def cmd_complete(args):
    """完成迭代"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-id", default=None)
    parser.add_argument("--outputs", default="")
    parser.add_argument("--problems", default="")
    parser.add_argument("--next-start", default="")
    parsed, _ = parser.parse_known_args(args)

    complete_iteration(
        page_id=parsed.page_id,
        outputs=parsed.outputs,
        problems=parsed.problems,
        next_start=parsed.next_start
    )


def cmd_milestone(args):
    """管理里程碑"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--name", default=None)
    parser.add_argument("--version", default="v0.1")
    parser.add_argument("--status", default=None)
    parser.add_argument("--progress", type=int, default=None)
    parser.add_argument("--days", type=int, default=5)
    parsed, _ = parser.parse_known_args(args)

    if parsed.create and parsed.name:
        create_milestone(
            name=parsed.name,
            version=parsed.version,
            estimated_days=parsed.days
        )
    elif parsed.progress is not None and parsed.name:
        update_milestone_progress(parsed.name, parsed.progress)
    elif parsed.status and parsed.name:
        print(f"状态更新: {parsed.name} -> {parsed.status}")
    else:
        print("用法:")
        print("  python iteration_tracker.py milestone --create --name 'v0.2' --days 10")
        print("  python iteration_tracker.py milestone --name 'v0.2' --progress 50")


def main():
    if len(sys.argv) < 2:
        cmd_status()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "status": cmd_status,
        "new": cmd_new,
        "complete": cmd_complete,
        "milestone": cmd_milestone,
        "ls": lambda a: cmd_status()  # alias
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: status, new, complete, milestone")


if __name__ == "__main__":
    main()
