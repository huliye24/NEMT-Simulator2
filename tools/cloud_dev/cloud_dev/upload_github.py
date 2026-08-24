#!/usr/bin/env python3
"""
上传到GitHub Release，然后云服务器下载解压
流程：
1. 本地压缩zip
2. 上传到GitHub Release
3. 云服务器下载并解压
"""

import zipfile
import os
import time
import paramiko
from pathlib import Path

LOCAL_BASE = Path(r"E:\NEMT Simulator")
ZIP_FILE = r"E:\NEMT_Simulator_Full.zip"

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
REMOTE_DIR = "/root/nemt-workspace"

# GitHub配置 - 请填入你的信息
GITHUB_TOKEN = ""  # 你的GitHub Personal Access Token
GITHUB_USER = ""   # 你的GitHub用户名
GITHUB_REPO = "NEMT-Simulator"  # 仓库名

SKIP_DIRS = {'.git', '__pycache__', '.cursor', '.venv', 'venv',
             '.pytest_cache', '.ruff_cache', 'node_modules', '.idea',
             'dist', 'build'}


def step1_create_zip():
    """步骤1: 创建压缩包"""
    print("=" * 70)
    print("  步骤1: 创建压缩包")
    print("=" * 70)
    
    if Path(ZIP_FILE).exists():
        os.remove(ZIP_FILE)
        print("删除旧压缩包...")
    
    count = 0
    
    with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(LOCAL_BASE):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            for f in files:
                local_file = Path(root) / f
                rel_path = local_file.relative_to(LOCAL_BASE)
                zf.write(local_file, rel_path)
                count += 1
                
                if count % 1000 == 0:
                    print(f"  已添加 {count} 个文件...")
    
    zip_size = Path(ZIP_FILE).stat().st_size
    print(f"\n完成: {count} 个文件, 大小: {zip_size / 1024 / 1024:.1f} MB")
    
    return ZIP_FILE


def step2_upload_github(zip_path):
    """步骤2: 上传到GitHub Release"""
    print("\n" + "=" * 70)
    print("  步骤2: 上传到GitHub Release")
    print("=" * 70)
    
    if not GITHUB_TOKEN or not GITHUB_USER:
        print("错误: 请设置 GITHUB_TOKEN 和 GITHUB_USER")
        return None
    
    import requests
    
    # 获取仓库信息
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # 检查仓库是否存在，不存在则创建
    repo_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}"
    r = requests.get(repo_url, headers=headers)
    
    if r.status_code == 404:
        print("创建仓库...")
        requests.post("https://api.github.com/user/repos", 
                     headers=headers, 
                     json={"name": GITHUB_REPO, "private": True})
    
    # 创建或获取Release
    release_url = f"{repo_url}/releases"
    r = requests.get(release_url, headers=headers)
    
    # 创建新Release
    print("创建Release...")
    tag = f"full-backup-{time.strftime('%Y%m%d-%H%M%S')}"
    release_data = {
        "tag_name": tag,
        "name": f"完整备份 {time.strftime('%Y-%m-%d')}",
        "body": "NEMT Simulator 完整备份",
        "draft": False,
        "prerelease": False
    }
    
    r = requests.post(release_url, headers=headers, json=release_data)
    release = r.json()
    upload_url = release['upload_url'].replace('{?name,label}', f'?name={Path(zip_path).name}')
    
    # 上传文件
    print(f"上传 {Path(zip_path).name}...")
    print("(这可能需要几分钟，请耐心等待)")
    
    with open(zip_path, 'rb') as f:
        data = f.read()
    
    r = requests.post(
        upload_url,
        headers={**headers, "Content-Type": "application/zip"},
        data=data
    )
    
    if r.status_code in [200, 201]:
        release_url = r.json()['html_url']
        print(f"上传成功!")
        print(f"Release: {release_url}")
        return release_url
    else:
        print(f"上传失败: {r.status_code}")
        return None


def step3_cloud_download(release_url):
    """步骤3: 云服务器下载并解压"""
    print("\n" + "=" * 70)
    print("  步骤3: 云服务器下载并解压")
    print("=" * 70)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    
    # 获取下载链接
    import requests
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    releases = requests.get(f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest",
                            headers=headers).json()
    
    download_url = None
    for asset in releases.get('assets', []):
        if asset['name'].endswith('.zip'):
            download_url = asset['browser_download_url']
            break
    
    if not download_url:
        print("找不到下载链接")
        return
    
    print(f"下载链接: {download_url}")
    
    # 云服务器下载
    print("云服务器开始下载...")
    
    cmd = f'''
cd {REMOTE_DIR}
rm -rf NEMT_Simulator_Full.zip
wget -O NEMT_Simulator_Full.zip "{download_url}"
'''
    
    stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # 解压
    print("\n解压文件...")
    cmd = f'''
cd {REMOTE_DIR}
unzip -o NEMT_Simulator_Full.zip
rm NEMT_Simulator_Full.zip
find . -type f | wc -l
'''
    
    stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
    print(stdout.read().decode())
    
    client.close()
    print("完成!")


def main():
    start = time.time()
    
    # 1. 压缩
    zip_path = step1_create_zip()
    
    # 2. 上传GitHub
    release_url = step2_upload_github(zip_path)
    
    if release_url:
        # 3. 云端下载
        step3_cloud_download(release_url)
    
    elapsed = time.time() - start
    print("\n" + "=" * 70)
    print(f"  全部完成! 耗时: {elapsed/60:.1f} 分钟")
    print("=" * 70)


if __name__ == "__main__":
    main()
