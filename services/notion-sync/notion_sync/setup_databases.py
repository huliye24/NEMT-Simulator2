#!/usr/bin/env python3
"""
Notion 双向同步 - 数据库结构设置
=================================
创建 NEMT 项目所需的 Notion 数据库结构

数据库列表:
1. 愿景文档 (Vision) - 核心愿景文档
2. 决策记录 (Decisions) - 决策日志
3. 技术文档 (Technical) - 架构、技术债务等
4. 任务 (Tasks) - Agent 任务管理
5. 模板 (Templates) - 文档模板

使用方法:
    python notion_sync/setup_databases.py
"""

import os
import sys
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# 确保 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# 配置
# ============================================================================

# Notion API 配置
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
if not NOTION_TOKEN:
    env_path = os.path.join(os.path.dirname(__file__), "..", "quant-sync-server", ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                if line.startswith("NOTION_TOKEN="):
                    NOTION_TOKEN = line.split("=", 1)[1].strip()
                    break

if not NOTION_TOKEN:
    print("❌ 错误: 未找到 NOTION_TOKEN")
    print("请设置环境变量或在 .env 文件中配置 NOTION_TOKEN")
    sys.exit(1)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# 父页面 ID (愿景管理系统)
PARENT_PAGE_ID = "34717dca0dd280d78c7cd9f1cf0afa92"

# ============================================================================
# HTTP 客户端
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
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送 HTTP 请求"""
        url = f"{NOTION_API_BASE}/{endpoint}"
        headers = {k: v for k, v in self.headers.items()}
        
        if data:
            response = requests.request(method, url, headers=headers, json=data, timeout=30)
        else:
            response = requests.request(method, url, headers=headers, timeout=30)
        
        if response.status_code >= 400:
            print(f"❌ API 错误 ({response.status_code}): {response.text[:500]}")
            raise Exception(f"Notion API error: {response.status_code}")
        
        return response.json()
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        return self._request("POST", endpoint, data)
    
    def get(self, endpoint: str) -> Dict:
        return self._request("GET", endpoint)
    
    def patch(self, endpoint: str, data: Dict) -> Dict:
        return self._request("PATCH", endpoint, data)

# ============================================================================
# 数据库架构定义
# ============================================================================

@dataclass
class DatabaseSchema:
    """数据库架构定义"""
    name: str
    name_cn: str
    description: str
    schema: Dict[str, dict]
    icon: str = "📄"
    parent_id: Optional[str] = None
    database_id: Optional[str] = None

def create_database_schemas() -> List[DatabaseSchema]:
    """创建所有数据库架构"""
    
    schemas = [
        # 1. 愿景文档数据库
        DatabaseSchema(
            name="Vision",
            name_cn="愿景文档",
            description="NEMT 项目的核心愿景、原则和边界定义",
            icon="🎯",
            schema={
                "名称": {
                    "type": "title",
                    "name": "名称"
                },
                "状态": {
                    "type": "select",
                    "name": "状态",
                    "select_options": [
                        {"name": "起草中", "color": "yellow"},
                        {"name": "评审中", "color": "blue"},
                        {"name": "已批准", "color": "green"},
                        {"name": "已归档", "color": "gray"}
                    ]
                },
                "类型": {
                    "type": "select",
                    "name": "类型",
                    "select_options": [
                        {"name": "愿景", "color": "purple"},
                        {"name": "原则", "color": "blue"},
                        {"name": "边界", "color": "red"},
                        {"name": "目标", "color": "green"},
                        {"name": "决策框架", "color": "orange"}
                    ]
                },
                "维护者": {
                    "type": "select",
                    "name": "维护者",
                    "select_options": [
                        {"name": "Founder Agent", "color": "purple"},
                        {"name": "CEO Agent", "color": "red"},
                        {"name": "PM Agent", "color": "blue"}
                    ]
                },
                "Obsidian路径": {
                    "type": "url",
                    "name": "Obsidian路径"
                },
                "Notion路径": {
                    "type": "url",
                    "name": "Notion路径"
                },
                "最后同步": {
                    "type": "date",
                    "name": "最后同步"
                },
                "标签": {
                    "type": "multi_select",
                    "name": "标签",
                    "multi_select_options": [
                        {"name": "核心文档", "color": "red"},
                        {"name": "待同步", "color": "orange"},
                        {"name": "已同步", "color": "green"},
                        {"name": "需更新", "color": "yellow"}
                    ]
                }
            }
        ),
        
        # 2. 决策记录数据库
        DatabaseSchema(
            name="Decisions",
            name_cn="决策记录",
            description="项目决策记录，包含背景、方案、结论和影响分析",
            icon="⚖️",
            schema={
                "名称": {
                    "type": "title",
                    "name": "名称"
                },
                "日期": {
                    "type": "date",
                    "name": "日期"
                },
                "决策人": {
                    "type": "select",
                    "name": "决策人",
                    "select_options": [
                        {"name": "Founder Agent", "color": "purple"},
                        {"name": "CTO Agent", "color": "blue"},
                        {"name": "PM Agent", "color": "pink"},
                        {"name": "TechLead Agent", "color": "green"}
                    ]
                },
                "决策类型": {
                    "type": "select",
                    "name": "决策类型",
                    "select_options": [
                        {"name": "架构决策", "color": "blue"},
                        {"name": "技术选型", "color": "purple"},
                        {"name": "优先级", "color": "yellow"},
                        {"name": "资源分配", "color": "green"},
                        {"name": "边界调整", "color": "red"}
                    ]
                },
                "状态": {
                    "type": "select",
                    "name": "状态",
                    "select_options": [
                        {"name": "提议中", "color": "yellow"},
                        {"name": "已通过", "color": "green"},
                        {"name": "已拒绝", "color": "red"},
                        {"name": "待验证", "color": "blue"}
                    ]
                },
                "愿景对齐": {
                    "type": "checkbox",
                    "name": "愿景对齐"
                },
                "Obsidian路径": {
                    "type": "url",
                    "name": "Obsidian路径"
                },
                "最后同步": {
                    "type": "date",
                    "name": "最后同步"
                }
            }
        ),
        
        # 3. 技术文档数据库
        DatabaseSchema(
            name="Technical",
            name_cn="技术文档",
            description="架构文档、技术债务、技术原则等",
            icon="🔧",
            schema={
                "名称": {
                    "type": "title",
                    "name": "名称"
                },
                "类型": {
                    "type": "select",
                    "name": "类型",
                    "select_options": [
                        {"name": "架构", "color": "blue"},
                        {"name": "技术债务", "color": "red"},
                        {"name": "技术原则", "color": "purple"},
                        {"name": "技术雷达", "color": "yellow"},
                        {"name": "代码规范", "color": "green"},
                        {"name": "接口契约", "color": "orange"}
                    ]
                },
                "优先级": {
                    "type": "select",
                    "name": "优先级",
                    "select_options": [
                        {"name": "P1-紧急", "color": "red"},
                        {"name": "P2-重要", "color": "orange"},
                        {"name": "P3-正常", "color": "yellow"},
                        {"name": "P4-低", "color": "gray"}
                    ]
                },
                "状态": {
                    "type": "select",
                    "name": "状态",
                    "select_options": [
                        {"name": "待处理", "color": "gray"},
                        {"name": "进行中", "color": "yellow"},
                        {"name": "已完成", "color": "green"},
                        {"name": "已验证", "color": "blue"}
                    ]
                },
                "维护者": {
                    "type": "select",
                    "name": "维护者",
                    "select_options": [
                        {"name": "CTO Agent", "color": "blue"},
                        {"name": "TechLead Agent", "color": "green"}
                    ]
                },
                "Obsidian路径": {
                    "type": "url",
                    "name": "Obsidian路径"
                },
                "最后同步": {
                    "type": "date",
                    "name": "最后同步"
                }
            }
        ),
        
        # 4. 任务数据库
        DatabaseSchema(
            name="Tasks",
            name_cn="任务",
            description="Agent 任务管理",
            icon="📋",
            schema={
                "名称": {
                    "type": "title",
                    "name": "名称"
                },
                "状态": {
                    "type": "select",
                    "name": "状态",
                    "select_options": [
                        {"name": "待办", "color": "gray"},
                        {"name": "进行中", "color": "yellow"},
                        {"name": "已完成", "color": "green"},
                        {"name": "已取消", "color": "red"}
                    ]
                },
                "优先级": {
                    "type": "select",
                    "name": "优先级",
                    "select_options": [
                        {"name": "紧急", "color": "red"},
                        {"name": "高", "color": "orange"},
                        {"name": "中", "color": "yellow"},
                        {"name": "低", "color": "gray"}
                    ]
                },
                "负责人": {
                    "type": "select",
                    "name": "负责人",
                    "select_options": [
                        {"name": "Founder Agent", "color": "purple"},
                        {"name": "CEO Agent", "color": "red"},
                        {"name": "CTO Agent", "color": "blue"},
                        {"name": "PM Agent", "color": "pink"},
                        {"name": "TechLead Agent", "color": "green"}
                    ]
                },
                "截止日期": {
                    "type": "date",
                    "name": "截止日期"
                },
                "Obsidian路径": {
                    "type": "url",
                    "name": "Obsidian路径"
                },
                "最后同步": {
                    "type": "date",
                    "name": "最后同步"
                }
            }
        ),
        
        # 5. 模板数据库
        DatabaseSchema(
            name="Templates",
            name_cn="模板",
            description="文档模板库",
            icon="📝",
            schema={
                "名称": {
                    "type": "title",
                    "name": "名称"
                },
                "类型": {
                    "type": "select",
                    "name": "类型",
                    "select_options": [
                        {"name": "决策模板", "color": "blue"},
                        {"name": "周检模板", "color": "green"},
                        {"name": "偏离模板", "color": "red"},
                        {"name": "技术模板", "color": "purple"},
                        {"name": "任务模板", "color": "yellow"}
                    ]
                },
                "用途": {
                    "type": "rich_text",
                    "name": "用途"
                },
                "Obsidian路径": {
                    "type": "url",
                    "name": "Obsidian路径"
                },
                "最后同步": {
                    "type": "date",
                    "name": "最后同步"
                }
            }
        ),
        
        # 6. ADR 数据库 (架构决策记录)
        DatabaseSchema(
            name="ADR",
            name_cn="架构决策记录",
            description="Architecture Decision Records",
            icon="📜",
            schema={
                "名称": {
                    "type": "title",
                    "name": "名称"
                },
                "日期": {
                    "type": "date",
                    "name": "日期"
                },
                "状态": {
                    "type": "select",
                    "name": "状态",
                    "select_options": [
                        {"name": "提议", "color": "yellow"},
                        {"name": "已接受", "color": "green"},
                        {"name": "已废弃", "color": "red"},
                        {"name": "已被替代", "color": "gray"}
                    ]
                },
                "决策人": {
                    "type": "select",
                    "name": "决策人",
                    "select_options": [
                        {"name": "CTO Agent", "color": "blue"},
                        {"name": "TechLead Agent", "color": "green"}
                    ]
                },
                "Obsidian路径": {
                    "type": "url",
                    "name": "Obsidian路径"
                },
                "最后同步": {
                    "type": "date",
                    "name": "最后同步"
                }
            }
        )
    ]
    
    return schemas

# ============================================================================
# 数据库操作
# ============================================================================

def build_schema_properties(schema: Dict[str, dict]) -> Dict[str, dict]:
    """构建 Notion 数据库属性"""
    properties = {}

    for prop_name, prop_config in schema.items():
        prop_type = prop_config["type"]

        if prop_type == "title":
            properties[prop_name] = {"title": {}}
        elif prop_type == "rich_text":
            properties[prop_name] = {"rich_text": {}}
        elif prop_type == "select":
            options = prop_config.get("select_options", [])
            properties[prop_name] = {
                "select": {
                    "options": options
                }
            }
        elif prop_type == "multi_select":
            options = prop_config.get("multi_select_options", [])
            properties[prop_name] = {
                "multi_select": {
                    "options": options
                }
            }
        elif prop_type == "date":
            properties[prop_name] = {"date": {}}
        elif prop_type == "checkbox":
            properties[prop_name] = {"checkbox": {}}
        elif prop_type == "number":
            properties[prop_name] = {"number": {"format": "number"}}
        elif prop_type == "url":
            properties[prop_name] = {"url": {}}
        elif prop_type == "email":
            properties[prop_name] = {"email": {}}
        elif prop_type == "phone_number":
            properties[prop_name] = {"phone_number": {}}
        elif prop_type == "relation":
            # relation 类型：Notion API 不支持在 create 时指定 relation
            # 创建后需要手动配置 relation 属性
            # 这里先跳过，创建后会提示用户手动配置
            print(f"  ⚠️  relation 类型属性 '{prop_name}' 需要创建后手动配置")
            continue
        elif prop_type == "formula":
            properties[prop_name] = {"formula": {}}
        elif prop_type == "rollup":
            properties[prop_name] = {"rollup": {}}
        elif prop_type == "files":
            properties[prop_name] = {"files": {}}
        elif prop_type == "people":
            properties[prop_name] = {"people": {}}

    return properties

def create_database(client: NotionClient, schema: DatabaseSchema, parent_page_id: str) -> Optional[str]:
    """创建数据库"""
    print(f"\n{'='*60}")
    print(f"创建数据库: {schema.icon} {schema.name_cn} ({schema.name})")
    print(f"{'='*60}")
    
    # 构建请求数据
    data = {
        "parent": {
            "type": "page_id",
            "page_id": parent_page_id
        },
        "icon": {
            "type": "emoji",
            "emoji": schema.icon
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": f"{schema.icon} {schema.name_cn}"
                }
            }
        ],
        "properties": build_schema_properties(schema.schema),
        "description": schema.description
    }
    
    try:
        response = client.post("databases", data)
        database_id = response.get("id")
        
        if database_id:
            print(f"✅ 数据库创建成功!")
            print(f"   ID: {database_id}")
            print(f"   URL: https://notion.so/{database_id.replace('-', '')}")
            return database_id
        else:
            print(f"❌ 创建失败: {response}")
            return None
            
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return None

def list_existing_databases(client: NotionClient, parent_page_id: str) -> List[Dict]:
    """列出父页面下的现有数据库"""
    print("\n📋 检查现有数据库...")
    
    try:
        # 获取页面children
        response = client.get(f"blocks/{parent_page_id}/children")
        blocks = response.get("results", [])
        
        databases = []
        for block in blocks:
            if block.get("type") == "child_database":
                databases.append({
                    "id": block.get("id"),
                    "title": block.get("child_database", {}).get("title", [])
                })
        
        return databases
        
    except Exception as e:
        print(f"⚠️  检查失败: {e}")
        return []

def update_database(client: NotionClient, database_id: str, schema: DatabaseSchema) -> bool:
    """更新现有数据库属性"""
    print(f"\n更新数据库: {schema.name_cn}")
    
    # 构建新属性
    new_properties = build_schema_properties(schema.schema)
    
    data = {
        "properties": new_properties
    }
    
    try:
        client.patch(f"databases/{database_id}", data)
        print(f"✅ 更新成功")
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False

# ============================================================================
# 主函数
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="NEMT Notion 数据库结构设置")
    parser.add_argument("--extended", action="store_true",
                        help="使用扩展 schema（包含 conclusion/reason/quality 等字段）")
    parser.add_argument("--check", action="store_true",
                        help="仅检查现有数据库状态，不创建")
    parser.add_argument("--parent-id", type=str, default=None,
                        help="指定父页面 ID（覆盖配置）")
    args = parser.parse_args()

    print("=" * 70)
    print("🗄️  NEMT Notion 数据库结构设置")
    print("=" * 70)

    # 尝试加载跨平台配置
    config_loaded = False
    try:
        # 延迟导入，避免循环依赖
        import sys as _sys
        _sys.path.insert(0, str(__file__).rsplit('\\', 1)[0] if '\\' in __file__ else str(__file__).rsplit('/', 1)[0])
        from nemt_sync_config import get_config, get_notion_client, check_setup_status
        status = check_setup_status()
        if status["ready"]:
            config = get_config()
            NOTION_TOKEN = config.notion_token
            PARENT_PAGE_ID = args.parent_id or config.parent_page_id
            client = get_notion_client()
            config_loaded = True
            print(f"\n✅ 配置加载成功")
            print(f"   Token: {'✓ 已配置' if config.notion_token else '✗ 未配置'}")
            print(f"   数据库数: {len(config.database_ids)}")
            print(f"   父页面: {PARENT_PAGE_ID[:8]}...")
        else:
            print(f"\n⚠️  配置未就绪，使用默认配置")
            for issue in status["issues"]:
                print(f"   ❌ {issue['message']}")
            print(f"   修复: {issue['fix']}")
            NOTION_TOKEN = ""
            PARENT_PAGE_ID = args.parent_id or PARENT_PAGE_ID
            client = None
    except ImportError:
        print(f"\n⚠️  配置文件未找到，使用默认配置")
        NOTION_TOKEN = ""
        PARENT_PAGE_ID = args.parent_id or PARENT_PAGE_ID
        client = None

    # 如果没有 client，尝试用环境变量
    if client is None:
        if NOTION_TOKEN:
            client = NotionClient(NOTION_TOKEN)
        else:
            print("\n❌ 无法初始化 Notion 客户端")
            print("   请设置 NOTION_TOKEN 环境变量或创建 .env 文件")
            sys.exit(1)

    print(f"\n📄 父页面 ID: {PARENT_PAGE_ID}")

    # 构建 schema 列表
    if args.extended:
        print("\n📦 使用扩展 schema（Decision+Experience+Failure+Task）")
        try:
            from extended_schemas import get_all_schemas
            schemas_raw = get_all_schemas()
            from dataclasses import make_dataclass
            schemas = []
            for raw in schemas_raw:
                SchemaClass = make_dataclass(
                    'Schema_' + raw['name'],
                    [],
                    bases=(object,),
                    extras={
                        'name': raw['name'],
                        'name_cn': raw['name_cn'],
                        'description': raw['description'],
                        'icon': raw['icon'],
                        'schema': raw['schema']
                    }
                )
                schemas.append(SchemaClass())
        except ImportError as e:
            print(f"\n❌ 无法加载扩展 schema: {e}")
            sys.exit(1)
    else:
        schemas = create_database_schemas()

    # 保存数据库配置
    db_config = {
        "parent_page_id": PARENT_PAGE_ID,
        "databases": {},
        "created_at": datetime.now().isoformat()
    }

    for schema in schemas:
        if args.check:
            print(f"  检查: {schema.icon} {schema.name_cn} ({schema.name})")
            continue

        database_id = create_database(client, schema, PARENT_PAGE_ID)

        if database_id:
            db_config["databases"][schema.name] = {
                "id": database_id,
                "name_cn": schema.name_cn,
                "name": schema.name,
                "icon": schema.icon,
                "url": f"https://notion.so/{database_id.replace('-', '')}"
            }

    if args.check:
        print("\n✅ 检查完成")
        return

    # 保存配置
    config_path = os.path.join(os.path.dirname(__file__), "database_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(db_config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("📊 数据库创建汇总")
    print("="*70)
    
    for name, info in db_config["databases"].items():
        print(f"  {info['icon']} {info['name_cn']}: {info['url']}")
    
    print(f"\n💾 配置已保存到: {config_path}")
    print("="*70)

if __name__ == "__main__":
    main()
