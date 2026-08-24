"""
Cursor COS Memory System - 核心模块
将Cursor记忆同步到腾讯云COS，实现跨会话跨设备记忆

Usage:
    from cursor_memory_cos import MemoryCOS

    mem = MemoryCOS()
    mem.download_memory("electron")    # 下载项目记忆
    mem.upload_session(session_data)   # 上传会话记忆
"""

import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from qcloud_cos import CosConfig, CosS3Client, CosServiceError
from concurrent.futures import ThreadPoolExecutor

# 加载COS配置
env_path = Path(__file__).parent / "cos_sync.env"
load_dotenv(env_path)

COS_CONFIG = {
    'Region': os.getenv('COS_REGION', 'ap-guangzhou'),
    'SecretId': os.getenv('COS_SECRET_ID', ''),
    'SecretKey': os.getenv('COS_SECRET_KEY', ''),
    'Bucket': os.getenv('COS_BUCKET', 'cursormerory-1390947672'),
}

# 本地缓存目录
CACHE_DIR = Path(__file__).parent / ".cursor" / "memory-cos-cache"
INDEX_FILE = "memories/index.json"


class MemoryCOS:
    """COS记忆系统核心类"""

    def __init__(self):
        self.client = self._get_client()
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_client(self) -> CosS3Client:
        """获取COS客户端"""
        config = CosConfig(
            Region=COS_CONFIG['Region'],
            SecretId=COS_CONFIG['SecretId'],
            SecretKey=COS_CONFIG['SecretKey'],
        )
        return CosS3Client(config)

    def _cos_path(self, key: str) -> str:
        """生成COS路径"""
        return key if key.startswith('memories/') else f"memories/{key}"

    def download_file(self, cos_key: str, local_path: Path) -> bool:
        """下载单个文件"""
        try:
            self.client.download_file(
                Bucket=COS_CONFIG['Bucket'],
                Key=cos_key,
                DestFilePath=str(local_path)
            )
            return True
        except CosServiceError as e:
            print(f"[DOWNLOAD FAIL] {cos_key}: {e}")
            return False

    def upload_file(self, local_path: Path, cos_key: str) -> bool:
        """上传单个文件"""
        try:
            self.client.upload_file(
                Bucket=COS_CONFIG['Bucket'],
                Key=cos_key,
                LocalFilePath=str(local_path)
            )
            return True
        except Exception as e:
            print(f"[UPLOAD FAIL] {local_path} -> {cos_key}: {e}")
            return False

    def get_index(self) -> Dict[str, Any]:
        """获取全局索引"""
        local_index = self.cache_dir / "index.json"

        # 尝试下载最新索引
        try:
            if self.download_file(self._cos_path(INDEX_FILE), local_index):
                with open(local_index, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass

        # 返回默认索引
        return {
            "last_sync": datetime.now().isoformat(),
            "projects": {},
            "version": "1.0"
        }

    def update_index(self, project: str, session_count: int = None,
                     patterns_count: int = None, resolved_count: int = None) -> bool:
        """更新项目索引"""
        index = self.get_index()

        if project not in index.get("projects", {}):
            index["projects"][project] = {}

        proj_data = index["projects"][project]
        proj_data["last_session"] = datetime.now().strftime("%Y-%m-%d")

        if session_count is not None:
            proj_data["session_count"] = proj_data.get("session_count", 0) + 1
        if patterns_count is not None:
            proj_data["patterns_count"] = patterns_count
        if resolved_count is not None:
            proj_data["resolved_count"] = resolved_count

        index["last_sync"] = datetime.now().isoformat()

        # 保存到本地和COS
        local_index = self.cache_dir / "index.json"
        with open(local_index, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

        return self.upload_file(local_index, self._cos_path(INDEX_FILE))

    def download_project_memory(self, project: str) -> Dict[str, Any]:
        """下载项目记忆到本地缓存"""
        print(f"[MEMORY] Downloading memory for: {project}")

        project_dir = self.cache_dir / project
        project_dir.mkdir(parents=True, exist_ok=True)

        downloaded = {}

        # 下载 patterns.json
        patterns_key = f"memories/{project}/patterns.json"
        patterns_local = project_dir / "patterns.json"
        if self.download_file(patterns_key, patterns_local):
            with open(patterns_local, 'r', encoding='utf-8') as f:
                downloaded["patterns"] = json.load(f)
        else:
            downloaded["patterns"] = []

        # 下载 failures.json
        failures_key = f"memories/{project}/failures.json"
        failures_local = project_dir / "failures.json"
        if self.download_file(failures_key, failures_local):
            with open(failures_local, 'r', encoding='utf-8') as f:
                downloaded["failures"] = json.load(f)
        else:
            downloaded["failures"] = []

        # 下载最近的5个sessions
        sessions_dir = project_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        downloaded["recent_sessions"] = self._download_recent_sessions(project, sessions_dir, limit=5)

        print(f"[MEMORY] Downloaded: {len(downloaded.get('patterns', []))} patterns, "
              f"{len(downloaded.get('failures', []))} failures, "
              f"{len(downloaded.get('recent_sessions', []))} sessions")

        return downloaded

    def _download_recent_sessions(self, project: str, local_dir: Path, limit: int = 5) -> List[Dict]:
        """下载最近的会话"""
        sessions = []
        prefix = f"memories/{project}/sessions/"

        try:
            resp = self.client.list_objects(
                Bucket=COS_CONFIG['Bucket'],
                Prefix=prefix
            )
            objects = resp.get('Contents', [])

            # 按时间排序，取最近的
            sorted_objs = sorted(objects, key=lambda x: x.get('LastModified', ''), reverse=True)

            for obj in sorted_objs[:limit]:
                key = obj['Key']
                local_path = local_dir / Path(key).name

                if self.download_file(key, local_path):
                    try:
                        with open(local_path, 'r', encoding='utf-8') as f:
                            sessions.append(json.load(f))
                    except:
                        pass

        except CosServiceError:
            pass

        return sessions

    def upload_session(self, session_data: Dict[str, Any], project: str = None) -> bool:
        """上传会话记忆"""
        project = project or self._detect_project()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_key = f"memories/{project}/sessions/{timestamp}.json"

        # 保存到本地临时文件
        local_session = self.cache_dir / f"session_{timestamp}.json"
        with open(local_session, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # 上传到COS
        success = self.upload_file(local_session, session_key)

        # 清理本地临时文件
        if local_session.exists():
            local_session.unlink()

        # 更新索引
        if success:
            self.update_index(project, session_count=1)

        return success

    def add_pattern(self, project: str, pattern: Dict[str, Any]) -> bool:
        """添加成功模式"""
        patterns_local = self.cache_dir / project / "patterns.json"
        patterns_local.parent.mkdir(parents=True, exist_ok=True)

        patterns = []
        if patterns_local.exists():
            with open(patterns_local, 'r', encoding='utf-8') as f:
                patterns = json.load(f)

        # 检查是否已存在
        pattern_hash = hashlib.md5(
            (pattern.get('problem', '') + pattern.get('solution', '')).encode()
        ).hexdigest()

        for p in patterns:
            if hashlib.md5(
                (p.get('problem', '') + p.get('solution', '')).encode()
            ).hexdigest() == pattern_hash:
                p['occurrences'] = p.get('occurrences', 1) + 1
                p['last_seen'] = datetime.now().isoformat()
                break
        else:
            pattern['occurrences'] = 1
            pattern['first_seen'] = datetime.now().isoformat()
            pattern['last_seen'] = datetime.now().isoformat()
            patterns.append(pattern)

        with open(patterns_local, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)

        return self.upload_file(patterns_local, f"memories/{project}/patterns.json")

    def add_failure(self, project: str, failure: Dict[str, Any]) -> bool:
        """添加失败教训"""
        failures_local = self.cache_dir / project / "failures.json"
        failures_local.parent.mkdir(parents=True, exist_ok=True)

        failures = []
        if failures_local.exists():
            with open(failures_local, 'r', encoding='utf-8') as f:
                failures = json.load(f)

        failure['timestamp'] = datetime.now().isoformat()
        failures.append(failure)

        # 保留最近100条
        failures = failures[-100:]

        with open(failures_local, 'w', encoding='utf-8') as f:
            json.dump(failures, f, ensure_ascii=False, indent=2)

        return self.upload_file(failures_local, f"memories/{project}/failures.json")

    def query_patterns(self, project: str, keyword: str = None,
                       tags: List[str] = None) -> List[Dict]:
        """查询模式"""
        patterns_local = self.cache_dir / project / "patterns.json"

        if not patterns_local.exists():
            self.download_file(
                f"memories/{project}/patterns.json",
                patterns_local
            )

        if not patterns_local.exists():
            return []

        with open(patterns_local, 'r', encoding='utf-8') as f:
            patterns = json.load(f)

        results = patterns

        # 按关键词过滤
        if keyword:
            keyword = keyword.lower()
            results = [p for p in results if
                       keyword in p.get('problem', '').lower() or
                       keyword in p.get('solution', '').lower()]

        # 按标签过滤
        if tags:
            results = [p for p in results if
                       any(t in p.get('tags', []) for t in tags)]

        return results

    def _detect_project(self) -> str:
        """检测当前项目"""
        project_root = Path(__file__).parent

        # 检测主要项目
        projects = ['electron', 'nemt-os', 'nemt-go', 'frontend', 'backend']

        for proj in projects:
            if (project_root / proj).exists():
                return proj

        # 使用目录名
        return project_root.name.lower().replace(' ', '-')

    def sync_full(self, project: str = None) -> bool:
        """完整同步项目记忆"""
        project = project or self._detect_project()
        print(f"[SYNC] Full sync for: {project}")

        # 下载
        self.download_project_memory(project)

        # 上传本地缓存的patterns和failures
        patterns_local = self.cache_dir / project / "patterns.json"
        failures_local = self.cache_dir / project / "failures.json"

        if patterns_local.exists():
            self.upload_file(patterns_local, f"memories/{project}/patterns.json")

        if failures_local.exists():
            self.upload_file(failures_local, f"memories/{project}/failures.json")

        return True


def create_session_summary() -> Dict[str, Any]:
    """从会话创建摘要（需要外部调用时传入上下文）"""
    return {
        "timestamp": datetime.now().isoformat(),
        "project": Path(__file__).parent.name,
        "resolved": [],
        "failed": [],
        "patterns": [],
        "tools_used": [],
        "notes": ""
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Cursor COS Memory System')
    parser.add_argument('action', choices=['download', 'upload', 'sync', 'query'],
                        help='Action to perform')
    parser.add_argument('-p', '--project', help='Project name')
    parser.add_argument('-k', '--keyword', help='Search keyword')
    parser.add_argument('-t', '--tags', nargs='+', help='Filter by tags')

    args = parser.parse_args()
    mem = MemoryCOS()

    if args.action == 'download':
        mem.download_project_memory(args.project or mem._detect_project())
    elif args.action == 'upload':
        summary = create_session_summary()
        mem.upload_session(summary, args.project)
    elif args.action == 'sync':
        mem.sync_full(args.project)
    elif args.action == 'query':
        results = mem.query_patterns(
            args.project or mem._detect_project(),
            args.keyword,
            args.tags
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
