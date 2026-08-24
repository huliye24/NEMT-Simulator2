"""
Tencent Cloud COS Tool
Usage:
    python cos_sync.py list [prefix]
    python cos_sync.py sync <local_dir> [remote_dir]
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from qcloud_cos import CosConfig, CosS3Client, CosServiceError
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time


env_path = Path(__file__).parent / "cos_sync.env"
load_dotenv(env_path)

COS_CONFIG = {
    'Region': os.getenv('COS_REGION', 'ap-guangzhou'),
    'SecretId': os.getenv('COS_SECRET_ID', ''),
    'SecretKey': os.getenv('COS_SECRET_KEY', ''),
    'Bucket': os.getenv('COS_BUCKET', ''),
}

counter_lock = Lock()
uploaded = 0
failed = 0


def get_client():
    config = CosConfig(
        Region=COS_CONFIG['Region'],
        SecretId=COS_CONFIG['SecretId'],
        SecretKey=COS_CONFIG['SecretKey'],
    )
    return CosS3Client(config)


def upload_single(args):
    global uploaded, failed
    file_path, remote_path = args
    try:
        client = get_client()
        client.upload_file(
            Bucket=COS_CONFIG['Bucket'],
            Key=remote_path,
            LocalFilePath=str(file_path)
        )
        with counter_lock:
            uploaded += 1
            if uploaded % 5000 == 0:
                print(f"[PROGRESS] Uploaded: {uploaded}, Failed: {failed}", flush=True)
        return True
    except Exception:
        with counter_lock:
            failed += 1
        return False


def sync_full(local_dir, remote_dir='', max_workers=20):
    global uploaded, failed
    local_path = Path(local_dir)
    if not local_path.exists():
        print(f"[FAIL] Directory not found: {local_dir}")
        return

    print(f"[SCAN] Scanning {local_dir}...", flush=True)
    files = []
    for root, dirs, filenames in os.walk(local_path):
        for fname in filenames:
            fpath = Path(root) / fname
            rel = fpath.relative_to(local_path)
            rpath = f"{remote_dir}/{rel}" if remote_dir else str(rel)
            files.append((fpath, rpath))

    total = len(files)
    print(f"[INFO] Total: {total}, Workers: {max_workers}", flush=True)

    start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(upload_single, f) for f in files]
        for f in as_completed(futures):
            f.result()

    elapsed = time.time() - start
    print(f"[DONE] Success: {uploaded}, Failed: {failed}, Time: {elapsed:.1f}s", flush=True)


def list_files(prefix=''):
    client = get_client()
    try:
        resp = client.list_objects(Bucket=COS_CONFIG['Bucket'], Prefix=prefix)
        objs = resp.get('Contents', [])
        if not objs:
            print("[EMPTY]")
            return
        print(f"\ncos://{COS_CONFIG['Bucket']}/{prefix}")
        print("-" * 60)
        for obj in objs[:30]:
            size = int(obj.get('Size', 0))
            s = f"{size/1024:.1f}KB" if size < 1048576 else f"{size/1048576:.1f}MB"
            print(f"  {s:>10}  {obj['Key']}")
        if len(objs) > 30:
            print(f"  ... {len(objs) - 30} more")
        print("-" * 60)
        print(f"Total: {len(objs)} files")
    except CosServiceError as e:
        print(f"[FAIL] {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', nargs='?', default='list')
    parser.add_argument('path1', nargs='?')
    parser.add_argument('path2', nargs='?')
    parser.add_argument('-w', '--workers', type=int, default=20)
    args = parser.parse_args()

    if not COS_CONFIG['SecretId']:
        print("[ERROR] Missing credentials")
        return

    if args.action == 'sync':
        sync_full(args.path1 or '.', args.path2 or '', args.workers)
    else:
        list_files(args.path1 or '')


if __name__ == '__main__':
    main()
