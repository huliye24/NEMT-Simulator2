#!/usr/bin/env python3
"""
Quant-Sync-Server 配置模块
"""

import os
import json
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import dataclass, field


# ============================================================================
# 路径配置
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
MATLAB_ROOT = PROJECT_ROOT / "matlab"
MATLAB_SCRIPTS = MATLAB_ROOT / "scripts"
MATLAB_CORE = MATLAB_ROOT / "nemt_core"
QUANT_MVP = PROJECT_ROOT / "quant-mvp"
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class PathConfig:
    paths: Dict[str, Path] = field(default_factory=dict)

    def __post_init__(self):
        self.paths = {
            'project_root': PROJECT_ROOT,
            'matlab_root': MATLAB_ROOT,
            'matlab_scripts': MATLAB_SCRIPTS,
            'matlab_core': MATLAB_CORE,
            'quant_mvp': QUANT_MVP,
            'data_dir': DATA_DIR,
        }

    def get(self, key: str) -> Path:
        return self.paths.get(key, PROJECT_ROOT)


# ============================================================================
# Notion 配置
# ============================================================================
@dataclass
class NotionConfig:
    token: str = ""
    strategy_db_id: str = ""
    backtest_db_id: str = ""
    signal_db_id: str = ""

    def __post_init__(self):
        self.token = os.getenv("NOTION_TOKEN", "")
        self.strategy_db_id = os.getenv("NOTION_STRATEGY_DB", "")
        self.backtest_db_id = os.getenv("NOTION_BACKTEST_DB", "")
        self.signal_db_id = os.getenv("NOTION_SIGNAL_DB", "")


# ============================================================================
# MATLAB 配置
# ============================================================================
@dataclass
class MatlabConfig:
    engine_available: bool = False
    matlab_path: Optional[str] = None
    timeout: int = 300

    def __post_init__(self):
        try:
            import matlab.engine
            self.engine_available = True
        except ImportError:
            self.engine_available = False


# ============================================================================
# Redis 配置
# ============================================================================
@dataclass
class RedisConfig:
    host: str = "redis"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    def __post_init__(self):
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", "6379"))

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


# ============================================================================
# Go Server 配置
# ============================================================================
@dataclass
class GoServerConfig:
    host: str = "localhost"
    port: int = 8080
    grpc_port: int = 50051

    def __post_init__(self):
        self.host = os.getenv("GOSERVER_HOST", "localhost")
        self.port = int(os.getenv("GOSERVER_PORT", "8080"))
        self.grpc_port = int(os.getenv("GOSERVER_GRPC_PORT", "50051"))

    @property
    def http_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def grpc_url(self) -> str:
        return f"{self.host}:{self.grpc_port}"


# ============================================================================
# 量化参数默认值
# ============================================================================
@dataclass
class NEMTDefaultParams:
    alpha: float = 0.1
    beta: float = 1.0
    noise: float = 0.2
    dt: float = 0.01
    dx: float = 1.0
    steps: int = 50  # 减少步数提高速度
    n: int = 500

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alpha': self.alpha,
            'beta': self.beta,
            'noiseLevel': self.noise,
            'dt': self.dt,
            'dx': self.dx,
            'steps': self.steps,
            'n': self.n,
        }


# ============================================================================
# 主配置类
# ============================================================================
class Config:
    def __init__(self):
        # 重要: 先加载 .env 文件，再初始化其他配置
        self._load_env_overrides()
        
        self.paths = PathConfig()
        self.notion = NotionConfig()
        self.matlab = MatlabConfig()
        self.redis = RedisConfig()
        self.go_server = GoServerConfig()
        self.nemt_defaults = NEMTDefaultParams()

    def _load_env_overrides(self):
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value

    def get(self, section: str, key: str, default: Any = None) -> Any:
        section_obj = getattr(self, section, None)
        if section_obj:
            return getattr(section_obj, key, default)
        return default

    def to_dict(self) -> Dict[str, Any]:
        return {
            'paths': {k: str(v) for k, v in self.paths.paths.items()},
            'notion': {'configured': bool(self.notion.token)},
            'matlab': {'engine_available': self.matlab.engine_available},
            'redis': {'host': self.redis.host, 'port': self.redis.port},
            'go_server': {'http_url': self.go_server.http_url},
            'nemt_defaults': self.nemt_defaults.to_dict(),
        }


# 全局配置实例
config = Config()
