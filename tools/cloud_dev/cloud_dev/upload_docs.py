#!/usr/bin/env python3
"""上传docs目录的文档文件"""

import paramiko
from pathlib import Path

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"
LOCAL_BASE = Path(r"E:\NEMT Simulator")
REMOTE_BASE = "/root/nemt-workspace"


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    return client.open_sftp()


def create_dir(sftp, path):
    parts = path.strip('/').split('/')
    for i in range(1, len(parts) + 1):
        p = '/' + '/'.join(parts[:i])
        try:
            sftp.stat(p)
        except:
            sftp.mkdir(p)


def upload_docs():
    sftp = connect()
    docs_dir = LOCAL_BASE / "docs"
    
    files = list(docs_dir.glob("*.md"))
    print(f"找到 {len(files)} 个文档")
    
    success = 0
    for f in files:
        rel = f.relative_to(LOCAL_BASE)
        remote = f"{REMOTE_BASE}/{rel}"
        try:
            create_dir(sftp, str(rel.parent))
            sftp.put(str(f), remote)
            print(f"[OK] {rel.name}")
            success += 1
        except Exception as e:
            print(f"[失败] {rel.name}: {e}")
    
    print(f"\n完成: {success}/{len(files)}")
    sftp.close()


if __name__ == "__main__":
    upload_docs()
