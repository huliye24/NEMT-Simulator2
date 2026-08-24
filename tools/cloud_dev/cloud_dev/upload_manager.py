#!/usr/bin/env python3
"""
NEMT Simulator - 分步上传工具
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

PROGRESS_FILE = LOCAL_BASE / "cloud_dev" / "upload_progress.json"

# 定义上传步骤
STEPS = {
    1: ["README.md", "CLAUDE.md"],
    2: ["requirements.txt", "pyproject.toml"],
    3: [".env.example", ".coveragerc"],
    4: [".flake8", ".pre-commit-config.yaml", "pytest.ini"],
    5: ["Dockerfile", "docker-compose.yml", "docker-compose.prod.yml"],
    
    6: ["nemt_core.py", "main.py"],
    7: ["nemt_execution.py", "nemt_controller.py"],
    8: ["brain_layer.py"],
    9: ["nemt_state_machine.py"],
    10: ["nemt_risk.py", "nemt_signals.py"],
    11: ["nemt_probability_execution.py"],
    12: ["nemt_spatial_temporal.py"],
    13: ["nemt_volatility_model.py"],
    14: ["nemt_economic_analysis.py"],
    15: ["nemt_theory_config.json"],
    
    16: ["ai_safety.py", "ai_safety.bat"],
    17: ["ai_safety_emergency.bat", "ai_safety_rollback.bat"],
    18: ["ai_safety_snap.bat"],
    19: ["ai_sip_quick.bat", "ai_sip_startup.bat"],
    20: ["architecture_guard.py", "architecture_guard.bat"],
    21: ["direction_lock.py", "direction_lock.bat"],
    22: ["cognitive_router.py", "cognitive_router.bat"],
    23: ["state_recovery.py", "state_recovery.bat"],
    24: ["refactor_limit.py", "refactor_limit.bat"],
    
    25: ["cloud_status.py", "check_status.py"],
    26: ["cloud_server_connect.py", "cloud_ssh_connect.py"],
    27: ["check_cloud_server.py", "check_services.py"],
    28: ["cloud_view_code.py"],
    29: ["start_wede.py", "start_wede_v2.py"],
    30: ["install_wede.py", "fix_wede.py", "fix_wede_config.py"],
    
    31: ["data_fetcher.py", "binance_fetcher.py"],
    32: ["fetch_notion.py", "fetch_page2.py"],
    33: ["fetch_page_cloud.py", "fetch_page_save.py"],
    34: ["fetch_notion_v2.py", "fetch_notion_v3.py"],
    35: ["cloud_fetch_pages.py"],
    
    36: ["notion_setup.py", "notion_theory_sync.py"],
    37: ["create_notion_obsidian.py"],
    38: ["upload_nemt_notion.py", "upload_vision.py"],
    39: ["upload_all_notion.py", "upload_notion_tar.py"],
    40: ["simple_notion_structure.py"],
    
    41: ["test_api.go"],
    42: ["confirm_status.py"],
    43: ["debug_page.py", "fetch_founder_agent.py"],
    44: ["get_page_via_cloud.py", "quick_fetch_notion.py"],
    
    45: ["backtest_engine.py"],
    46: ["enhanced_phase_detector.py"],
    47: ["entropy_simulation.py", "entropy_sim_v2.py"],
    48: ["experiments.py", "benchmark.py"],
    49: ["entropy_simulation_result.txt"],
    
    50: ["backtest/__init__.py"],
    51: ["backtest/models/__init__.py", "backtest/models/market.py"],
    52: ["backtest/tests/__init__.py"],
    53: ["backtest/tests/test_loaders.py"],
    54: ["backtest/tests/test_models.py"],
    55: ["backtest/tests/test_processors.py"],
}


class UploadManager:
    def __init__(self):
        self.client = None
        self.sftp = None
        self.progress = self.load_progress()
        
    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
        self.sftp = self.client.open_sftp()
        
    def disconnect(self):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
    
    def load_progress(self):
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "current_step": 0,
            "completed": [],
            "failed": [],
            "last_update": None
        }
    
    def save_progress(self):
        self.progress["last_update"] = datetime.now().isoformat()
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
    def create_remote_dir(self, remote_path):
        """创建远程目录（如果不存在）"""
        parts = remote_path.strip('/').split('/')
        for i in range(1, len(parts) + 1):
            path = '/' + '/'.join(parts[:i])
            try:
                self.sftp.stat(path)
            except:
                try:
                    self.sftp.mkdir(path)
                except:
                    pass
    
    def upload_file(self, local_path, remote_path):
        """上传单个文件"""
        try:
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self.create_remote_dir(remote_dir)
            self.sftp.put(str(local_path), remote_path)
            return True, None
        except Exception as e:
            return False, str(e)
    
    def upload_step(self, step_num):
        """上传指定步骤的文件"""
        if step_num not in STEPS:
            return False, f"步骤 {step_num} 不存在"
        
        if step_num in self.progress["completed"]:
            print(f"  [跳过] 步骤 {step_num} 已完成")
            return True, None
        
        files = STEPS[step_num]
        print(f"\n{'='*60}")
        print(f"  步骤 {step_num}: 上传 {len(files)} 个文件")
        print(f"{'='*60}")
        
        success_count = 0
        fail_count = 0
        
        for file_path in files:
            local_file = LOCAL_BASE / file_path
            remote_file = f"{REMOTE_BASE}/{file_path}"
            
            if not local_file.exists():
                print(f"  [跳过] {file_path} (不存在)")
                continue
            
            success, error = self.upload_file(local_file, remote_file)
            if success:
                print(f"  [OK] {file_path}")
                success_count += 1
            else:
                print(f"  [失败] {file_path}: {error}")
                fail_count += 1
        
        if fail_count == 0:
            self.progress["completed"].append(step_num)
            self.progress["current_step"] = step_num
            self.save_progress()
            return True, None
        else:
            self.progress["failed"].append({"step": step_num, "files": files})
            self.save_progress()
            return False, f"成功 {success_count}, 失败 {fail_count}"
    
    def upload_range(self, start, end):
        """上传范围步骤"""
        print(f"\n{'#'*60}")
        print(f"  开始批量上传: 步骤 {start} - {end}")
        print(f"{'#'*60}\n")
        
        for step in range(start, end + 1):
            if step in self.progress["completed"]:
                print(f"[{step}] 已完成，跳过")
                continue
            
            self.upload_step(step)
        
        self.show_status()
    
    def upload_phase(self, phase):
        """按阶段上传"""
        phase_ranges = {
            1: (1, 30),    # 基础设施
            2: (31, 50),   # 数据与API
            3: (51, 70),   # 回测系统
            4: (71, 110),  # NEMT-OS核心
            5: (111, 140), # 前端与UI
            6: (141, 160), # 容器与部署
            7: (161, 180), # Go微服务
            8: (181, 200), # 工具与文档
        }
        
        if phase not in phase_ranges:
            return False, f"阶段 {phase} 不存在"
        
        start, end = phase_ranges[phase]
        print(f"\n阶段 {phase}: 步骤 {start} - {end}")
        self.upload_range(start, end)
        return True, None
    
    def show_status(self):
        """显示上传状态"""
        completed = len(self.progress["completed"])
        total = len(STEPS)
        failed = len(self.progress.get("failed", []))
        
        print(f"\n{'='*60}")
        print(f"  上传状态")
        print(f"{'='*60}")
        print(f"  总步骤: {total}")
        print(f"  已完成: {completed} ({completed*100//total}%)")
        print(f"  失败: {failed}")
        print(f"  当前: 步骤 {self.progress['current_step']}")
        print(f"  最后更新: {self.progress.get('last_update', 'N/A')}")
        print(f"{'='*60}")
        
        if completed < total:
            next_step = min([s for s in STEPS.keys() if s not in self.progress["completed"]], default=None)
            if next_step:
                print(f"  下一未完成步骤: {next_step}")
                print(f"  待上传文件: {', '.join(STEPS[next_step][:3])}{'...' if len(STEPS[next_step]) > 3 else ''}")


def main():
    manager = UploadManager()
    
    try:
        manager.connect()
        print("已连接到云端服务器")
    except Exception as e:
        print(f"连接失败: {e}")
        sys.exit(1)
    
    # 解析命令
    if len(sys.argv) < 2:
        manager.show_status()
        print("\n用法:")
        print("  python upload_manager.py status              # 显示状态")
        print("  python upload_manager.py step N              # 上传步骤N")
        print("  python upload_manager.py range N M           # 上传步骤N到M")
        print("  python upload_manager.py phase N             # 上传阶段N")
        print("  python upload_manager.py next                # 上传下一个未完成步骤")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "status":
        manager.show_status()
    
    elif cmd == "step" and len(sys.argv) >= 3:
        step = int(sys.argv[2])
        success, msg = manager.upload_step(step)
        if not success:
            print(f"失败: {msg}")
    
    elif cmd == "range" and len(sys.argv) >= 4:
        start = int(sys.argv[2])
        end = int(sys.argv[3])
        manager.upload_range(start, end)
    
    elif cmd == "phase" and len(sys.argv) >= 3:
        phase = int(sys.argv[2])
        manager.upload_phase(phase)
    
    elif cmd == "next":
        next_step = manager.progress["current_step"] + 1
        if next_step in STEPS:
            manager.upload_step(next_step)
        else:
            print("所有步骤已完成!")
    
    else:
        print("未知命令")
    
    manager.disconnect()


if __name__ == "__main__":
    main()
