#!/usr/bin/env python3
"""
NEMT Simulator - 快速上传脚本
简单命令，上传下一个批次
"""

import os
import sys
import json
import paramiko
from datetime import datetime
from pathlib import Path

# 配置
HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_BASE = Path(r"E:\NEMT Simulator")
REMOTE_BASE = "/root/nemt-workspace"

# 定义上传批次（简化版，每批多个文件）
BATCHES = {
    # 第一批：核心配置
    1: ["README.md", "CLAUDE.md", "requirements.txt", "pyproject.toml", ".env.example"],
    2: [".coveragerc", ".flake8", ".pre-commit-config.yaml", "pytest.ini"],
    3: ["Dockerfile", "docker-compose.yml", "docker-compose.prod.yml"],
    
    # 第二批：NEMT核心
    4: ["nemt_core.py", "main.py", "nemt_execution.py", "nemt_controller.py"],
    5: ["brain_layer.py", "nemt_state_machine.py"],
    6: ["nemt_risk.py", "nemt_signals.py", "nemt_probability_execution.py"],
    7: ["nemt_spatial_temporal.py", "nemt_volatility_model.py", "nemt_economic_analysis.py"],
    8: ["nemt_theory_config.json"],
    
    # 第三批：AI安全
    9: ["ai_safety.py", "ai_safety.bat", "ai_safety_emergency.bat", "ai_safety_rollback.bat"],
    10: ["ai_safety_snap.bat", "ai_sip_quick.bat", "ai_sip_startup.bat"],
    11: ["architecture_guard.py", "architecture_guard.bat"],
    12: ["direction_lock.py", "direction_lock.bat", "cognitive_router.py", "cognitive_router.bat"],
    13: ["state_recovery.py", "state_recovery.bat", "refactor_limit.py", "refactor_limit.bat"],
    
    # 第四批：云端连接
    14: ["cloud_status.py", "check_status.py", "cloud_server_connect.py"],
    15: ["cloud_ssh_connect.py", "check_cloud_server.py", "check_services.py"],
    16: ["cloud_view_code.py", "start_wede.py", "start_wede_v2.py"],
    17: ["install_wede.py", "fix_wede.py", "fix_wede_config.py", "fix_wede_password.py"],
    
    # 第五批：数据获取
    18: ["data_fetcher.py", "binance_fetcher.py"],
    19: ["fetch_notion.py", "fetch_page2.py", "fetch_page_cloud.py"],
    20: ["fetch_page_save.py", "fetch_notion_v2.py", "fetch_notion_v3.py"],
    21: ["cloud_fetch_pages.py", "confirm_status.py", "debug_page.py"],
    
    # 第六批：Notion同步
    22: ["notion_setup.py", "notion_theory_sync.py", "create_notion_obsidian.py"],
    23: ["upload_nemt_notion.py", "upload_vision.py", "upload_all_notion.py"],
    24: ["simple_notion_structure.py", "fetch_founder_agent.py", "get_page_via_cloud.py"],
    
    # 第七批：测试与工具
    25: ["test_api.go", "quick_fetch_notion.py"],
    26: ["backtest_engine.py", "enhanced_phase_detector.py"],
    27: ["entropy_simulation.py", "entropy_sim_v2.py", "experiments.py"],
    28: ["benchmark.py", "entropy_simulation_result.txt"],
    
    # 第八批：回测模块
    29: ["backtest/__init__.py", "backtest/models/__init__.py", "backtest/models/market.py"],
    30: ["backtest/tests/__init__.py", "backtest/tests/test_loaders.py", "backtest/tests/test_models.py"],
    31: ["backtest/tests/test_processors.py"],
    
    # 第九批：文档
    32: ["SPEC.md", "PRD.md", "TASKS.md", "FLOWS.md"],
    33: ["CHANGELOG.md", "LICENSE", "CODE_REVIEW_CHECKLIST.md"],
    34: ["SECURITY_AUDIT_REPORT.md", "SECURITY_FIX_REPORT.md"],
    
    # 第十批：大目录（需要特殊处理）
    35: ["docs/*.md"],  # 特殊处理
    36: ["data/"],  # 特殊处理
    37: ["output/"],  # 特殊处理
    38: ["matlab_data/"],  # 特殊处理
    39: ["results/"],  # 特殊处理
}

PROGRESS_FILE = LOCAL_BASE / "cloud_dev" / "batch_progress.json"


class QuickUploader:
    def __init__(self):
        self.client = None
        self.sftp = None
        self.progress = self.load_progress()
        
    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
        self.sftp = self.client.open_sftp()
        print("已连接云端服务器")
        
    def disconnect(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
    
    def load_progress(self):
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"current_batch": 0, "completed": [], "failed": []}
    
    def save_progress(self):
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2)
    
    def upload_file(self, local_path, remote_path):
        try:
            remote_dir = os.path.dirname(remote_path)
            parts = remote_dir.strip('/').split('/')
            for i in range(1, len(parts) + 1):
                p = '/' + '/'.join(parts[:i])
                try:
                    self.sftp.stat(p)
                except:
                    self.sftp.mkdir(p)
            
            self.sftp.put(str(local_path), remote_path)
            return True
        except Exception as e:
            print(f"    错误: {e}")
            return False
    
    def upload_batch(self, batch_num):
        if batch_num not in BATCHES:
            print(f"批次 {batch_num} 不存在")
            return False
        
        if batch_num in self.progress["completed"]:
            print(f"批次 {batch_num} 已完成，跳过")
            return True
        
        files = BATCHES[batch_num]
        print(f"\n{'='*60}")
        print(f"  批次 {batch_num}: 上传 {len(files)} 个文件/目录")
        print(f"{'='*60}")
        
        success = 0
        failed = 0
        
        for item in files:
            if item.endswith('/'):
                # 目录
                print(f"\n  [目录] {item}")
                local_dir = LOCAL_BASE / item
                if not local_dir.exists():
                    print(f"    不存在，跳过")
                    continue
                
                for root, dirs, filenames in os.walk(local_dir):
                    for filename in filenames:
                        local_file = Path(root) / filename
                        rel_path = local_file.relative_to(LOCAL_BASE)
                        remote_file = f"{REMOTE_BASE}/{rel_path}"
                        if self.upload_file(local_file, remote_file):
                            print(f"    [OK] {rel_path}")
                            success += 1
                        else:
                            failed += 1
            elif '*' in item:
                # 通配符
                pattern = item.replace('*', '')
                print(f"\n  [模式] {item}")
                local_dir = LOCAL_BASE / pattern
                if not local_dir.exists():
                    print(f"    不存在，跳过")
                    continue
                
                for f in local_dir.glob('*'):
                    if f.is_file():
                        rel_path = f.relative_to(LOCAL_BASE)
                        remote_file = f"{REMOTE_BASE}/{rel_path}"
                        if self.upload_file(f, remote_file):
                            print(f"    [OK] {rel_path}")
                            success += 1
                        else:
                            failed += 1
            else:
                # 单个文件
                local_file = LOCAL_BASE / item
                remote_file = f"{REMOTE_BASE}/{item}"
                
                if not local_file.exists():
                    print(f"  [跳过] {item} (不存在)")
                    continue
                
                if self.upload_file(local_file, remote_file):
                    print(f"  [OK] {item}")
                    success += 1
                else:
                    failed += 1
        
        if failed == 0:
            self.progress["completed"].append(batch_num)
            self.progress["current_batch"] = batch_num
            self.save_progress()
            print(f"\n批次 {batch_num} 完成! ({success} 个文件)")
            return True
        else:
            print(f"\n批次 {batch_num} 完成! 成功 {success}, 失败 {failed}")
            return False
    
    def upload_next(self):
        next_batch = self.progress["current_batch"] + 1
        if next_batch > max(BATCHES.keys()):
            print("所有批次已完成!")
            return True
        return self.upload_batch(next_batch)
    
    def upload_all_remaining(self):
        for batch_num in sorted(BATCHES.keys()):
            if batch_num not in self.progress["completed"]:
                self.upload_batch(batch_num)
    
    def status(self):
        total = len(BATCHES)
        done = len(self.progress["completed"])
        print(f"\n{'='*60}")
        print(f"  上传进度")
        print(f"{'='*60}")
        print(f"  总批次: {total}")
        print(f"  已完成: {done} ({done*100//total}%)")
        print(f"  当前: 批次 {self.progress['current_batch']}")
        if done < total:
            next_batch = min([b for b in BATCHES.keys() if b not in self.progress["completed"]])
            print(f"  下一批次: {next_batch} - {BATCHES[next_batch][:2]}{'...' if len(BATCHES[next_batch]) > 2 else ''}")
        print(f"{'='*60}")


def main():
    uploader = QuickUploader()
    
    try:
        uploader.connect()
    except Exception as e:
        print(f"连接失败: {e}")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        uploader.status()
        print("\n命令:")
        print("  python quick_upload.py status    # 查看进度")
        print("  python quick_upload.py next     # 上传下一个批次")
        print("  python quick_upload.py batch N  # 上传批次N")
        print("  python quick_upload.py all      # 上传所有剩余")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "status":
        uploader.status()
    elif cmd == "next":
        uploader.upload_next()
    elif cmd == "batch" and len(sys.argv) >= 3:
        uploader.upload_batch(int(sys.argv[2]))
    elif cmd == "all":
        uploader.upload_all_remaining()
    else:
        print("未知命令")
    
    uploader.disconnect()


if __name__ == "__main__":
    main()
