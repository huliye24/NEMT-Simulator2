# Copyright 2026 NEMT Lab
#
# NEMT Sync 跨平台配置文件
# ============================
#
# 所有路径使用 pathlib，自动适配 Windows/macOS/Linux
# 所有敏感配置从此文件读取，不再硬编码
#
# 使用方法：
#   from nemt_sync_config import config, get_client, PROJECT_ROOT, OBSIDIAN_ROOT
#
# 首次设置：
#   1. 复制 .env.example 为 .env
#   2. 填入 NOTION_TOKEN 和数据库 ID
#   3. python notion_sync/setup_databases.py  # 创建数据库
#   4. python notion_sync/initial_sync.py    # 首次同步
#

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ============================================================================
# 路径配置（跨平台）
# ============================================================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 同步根目录
SYNC_ROOT = PROJECT_ROOT / "notion_sync"

# Obsidian 仓库根目录
OBSIDIAN_ROOT = PROJECT_ROOT / "NEMT_Agent_System"

# 本地回退存储目录（Notion 不可用时）
FALLBACK_ROOT = SYNC_ROOT / "local_fallback"
FALLBACK_DECISIONS = FALLBACK_ROOT / "decisions"
FALLBACK_EXPERIENCES = FALLBACK_ROOT / "experiences"
FALLBACK_TASKS = FALLBACK_ROOT / "tasks"

# 状态文件
STATE_FILE = SYNC_ROOT / "sync_state.json"
LIVE_STATE_FILE = SYNC_ROOT / "live_sync_state.json"

# 数据库配置文件
DATABASE_CONFIG_FILE = SYNC_ROOT / "database_config.json"

# .env 文件查找路径
_ENV_PATHS = [
    SYNC_ROOT / ".env",
    PROJECT_ROOT / ".env",
    Path("E:\\NEMT Simulator\\.env"),  # Windows 显式路径
]


# ============================================================================
# 配置加载
# ============================================================================

@dataclass
class SyncConfig:
    """NEMT Sync 配置"""
    notion_token: str = ""
    notion_version: str = "2022-06-28"
    notion_api_base: str = "https://api.notion.com/v1"

    # Notion 数据库 ID（从 database_config.json 加载）
    parent_page_id: str = "34717dca0dd280d78c7cd9f1cf0afa92"
    database_ids: dict = field(default_factory=dict)

    # Obsidian 同步路径
    obsidian_nemt_notion: Path = field(default_factory=lambda: OBSIDIAN_ROOT / "NEMT_Notion")
    obsidian_nemt_agent: Path = field(default_factory=lambda: OBSIDIAN_ROOT / "NEMT_Agent_System")
    obsidian_vision: Path = field(default_factory=lambda: OBSIDIAN_ROOT / "NEMT_Vision")

    # 同步参数
    sync_interval_seconds: int = 180  # 实时同步轮询间隔
    batch_size: int = 100

    # 调试模式
    debug: bool = False

    def is_ready(self) -> bool:
        """检查配置是否就绪"""
        return bool(self.notion_token)


def _find_env_file() -> Optional[Path]:
    """查找 .env 文件（跨平台）"""
    for path in _ENV_PATHS:
        if path.exists():
            return path
    return None


def _load_env() -> dict:
    """加载 .env 文件"""
    env_path = _find_env_file()
    if not env_path:
        return {}

    env_vars = {}
    try:
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception:
        pass
    return env_vars


def _load_database_config() -> dict:
    """加载数据库配置"""
    if not DATABASE_CONFIG_FILE.exists():
        return {}

    try:
        import json
        with open(DATABASE_CONFIG_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _build_config() -> SyncConfig:
    """构建配置对象"""
    env_vars = _load_env()
    db_config = _load_database_config()

    # 从数据库配置中提取 ID
    database_ids = {}
    if "databases" in db_config:
        for db in db_config["databases"]:
            name = db.get("name", "")
            db_id = db.get("database_id", "")
            if name and db_id:
                database_ids[name] = db_id

    return SyncConfig(
        notion_token=env_vars.get("NOTION_TOKEN", ""),
        notion_version=env_vars.get("NOTION_VERSION", "2022-06-28"),
        parent_page_id=env_vars.get("PARENT_PAGE_ID", "34717dca0dd280d78c7cd9f1cf0afa92"),
        database_ids=database_ids,
        debug=env_vars.get("DEBUG", "").lower() in ("1", "true", "yes"),
    )


# ============================================================================
# 单例配置对象
# ============================================================================

_config: Optional[SyncConfig] = None


def get_config() -> SyncConfig:
    """获取配置单例"""
    global _config
    if _config is None:
        _config = _build_config()
    return _config


def reload_config() -> SyncConfig:
    """重新加载配置"""
    global _config
    _config = _build_config()
    return _config


def reset_config() -> None:
    """重置配置（用于测试）"""
    global _config
    _config = None


# ============================================================================
# Notion Client 工厂函数
# ============================================================================

def get_notion_client() -> 'NotionClient':
    """获取 Notion API 客户端"""
    from setup_databases import NotionClient as SetupClient
    config = get_config()
    if not config.notion_token:
        raise ValueError(
            "NOTION_TOKEN 未配置。\n"
            "请复制 notion_sync/.env.example 为 notion_sync/.env，"
            "并填入您的 Notion Integration Token。\n"
            f"查找路径: {[str(p) for p in _ENV_PATHS]}"
        )
    return SetupClient(config.notion_token)


def get_database_id(name: str) -> Optional[str]:
    """获取指定名称的数据库 ID"""
    return get_config().database_ids.get(name)


# ============================================================================
# 初始化检查
# ============================================================================

def check_setup_status() -> dict:
    """
    检查系统就绪状态
    返回: {ready: bool, issues: list, warnings: list}
    """
    config = get_config()
    issues = []
    warnings = []

    # 检查 Token
    if not config.notion_token:
        issues.append({
            "severity": "error",
            "component": "notion_token",
            "message": "NOTION_TOKEN 未配置",
            "fix": "复制 notion_sync/.env.example 为 notion_sync/.env 并填入 Token"
        })

    # 检查数据库配置
    if not config.database_ids:
        warnings.append({
            "severity": "warning",
            "component": "database_config",
            "message": f"数据库未创建或配置缺失 ({DATABASE_CONFIG_FILE})",
            "fix": "运行 python notion_sync/setup_databases.py"
        })
    else:
        warnings.append({
            "severity": "info",
            "component": "database_config",
            "message": f"已配置 {len(config.database_ids)} 个数据库",
        })

    # 检查 Obsidian 目录
    for name, path in [
        ("NEMT_Agent_System", OBSIDIAN_ROOT),
        ("decisions fallback", FALLBACK_DECISIONS),
        ("experiences fallback", FALLBACK_EXPERIENCES),
    ]:
        if not path.exists():
            warnings.append({
                "severity": "warning",
                "component": "obsidian_path",
                "message": f"{name} 目录不存在: {path}",
                "fix": f"将自动创建"
            })

    return {
        "ready": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "config": {
            "token_configured": bool(config.notion_token),
            "database_count": len(config.database_ids),
            "parent_page_id": config.parent_page_id,
        }
    }


# ============================================================================
# CLI 入口
# ============================================================================

    if __name__ == "__main__":
        import sys
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

        print("=" * 60)
        print("NEMT Sync Configuration Check")
        print("=" * 60)

        status = check_setup_status()

        print(f"\n项目路径: {PROJECT_ROOT}")
        print(f"同步路径: {SYNC_ROOT}")
        print(f"数据库配置: {DATABASE_CONFIG_FILE}")
        print(f"Parent Page: {status['config']['parent_page_id']}")

        if status["ready"]:
            print("\n[OK] 系统就绪")
        else:
            print("\n[FAIL] 系统未就绪")
            for issue in status["issues"]:
                print(f"  [X] {issue['message']}")
                print(f"     修复: {issue['fix']}")

        for warning in status["warnings"]:
            if warning["severity"] == "warning":
                print(f"  [!] {warning['message']}")
                print(f"     修复: {warning['fix']}")
            else:
                print(f"  [i] {warning['message']}")

        print("\n" + "=" * 60)
