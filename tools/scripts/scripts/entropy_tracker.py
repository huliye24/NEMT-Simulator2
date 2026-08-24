#!/usr/bin/env python3
"""
Entropy Tracker - 监控 NEMT 项目结构熵
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class EntropyTracker:
    """结构熵追踪器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.data_dir = self.project_root / "data" / "entropy"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.data_dir / "entropy_log.json"
    
    def count_files(self, directory: Path) -> int:
        """统计目录下的 Python 文件数"""
        if not directory.exists():
            return 0
        return len(list(directory.rglob("*.py")))
    
    def list_directories(self, directory: Path) -> List[str]:
        """列出所有子目录"""
        if not directory.exists():
            return []
        return [d.name for d in directory.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    def check_duplicate_dirs(self, base_dir: Path) -> List[Dict[str, str]]:
        """检查重复目录（不区分大小写）"""
        if not base_dir.exists():
            return []
        
        dirs = {}
        duplicates = []
        
        for d in base_dir.iterdir():
            if d.is_dir() and not d.name.startswith('.'):
                key = d.name.lower()
                if key in dirs:
                    duplicates.append({
                        "original": str(dirs[key]),
                        "duplicate": str(d)
                    })
                else:
                    dirs[key] = d
        
        return duplicates
    
    def get_directory_structure(self, nemt_dir: Path) -> Dict[str, Any]:
        """获取目录结构快照"""
        structure = {
            "timestamp": datetime.now().isoformat(),
            "subdirs": self.list_directories(nemt_dir),
            "total_py_files": self.count_files(nemt_dir),
            "duplicates": self.check_duplicate_dirs(nemt_dir)
        }
        return structure
    
    def log_entropy(self) -> Dict[str, Any]:
        """记录当前熵状态"""
        nemt_dir = self.project_root / "nemt_os" / "nemt"
        
        snapshot = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nemt_dir_structure": self.get_directory_structure(nemt_dir),
            "health_score": self._calculate_health_score(nemt_dir)
        }
        
        # 保存到日志
        logs = []
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        logs.append(snapshot)
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        return snapshot
    
    def _calculate_health_score(self, nemt_dir: Path) -> float:
        """计算结构健康分 (0-100)"""
        score = 100.0
        
        # 检查重复目录 (扣分)
        duplicates = self.check_duplicate_dirs(nemt_dir)
        score -= len(duplicates) * 10
        
        # 检查 __init__.py 完整性
        expected_dirs = ['core', 'config', 'storage', 'market_providers']
        for d in expected_dirs:
            init_file = nemt_dir / d / "__init__.py"
            if not init_file.exists():
                score -= 5
        
        return max(0, min(100, score))
    
    def print_report(self):
        """打印熵报告"""
        snapshot = self.log_entropy()
        
        print("=" * 60)
        print("NEMT 结构熵报告")
        print("=" * 60)
        print(f"时间: {snapshot['date']}")
        print(f"健康分: {snapshot['health_score']:.1f}/100")
        
        struct = snapshot['nemt_dir_structure']
        print(f"\n子目录数: {len(struct['subdirs'])}")
        print(f"Python 文件总数: {struct['total_py_files']}")
        
        if struct['duplicates']:
            print(f"\n发现 {len(struct['duplicates'])} 个重复目录:")
            for dup in struct['duplicates']:
                print(f"  - {dup['original']} <-> {dup['duplicate']}")
        else:
            print("\n[OK] 无重复目录")
        
        print("=" * 60)


if __name__ == "__main__":
    tracker = EntropyTracker()
    tracker.print_report()
