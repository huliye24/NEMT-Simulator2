#!/usr/bin/env python3
"""
COS Sync Script - 同步数据到腾讯云COS

将本地CSV数据同步到COS存储

Usage:
    python scripts/sync_to_cos.py --local-dir ./data/us_stocks/daily --remote-dir us_stocks/daily
    python scripts/sync_to_cos.py --local-dir ./data --remote-dir us_stocks --dry-run
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """同步结果"""
    local_path: str
    remote_path: str
    success: bool
    size: int
    error: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class SyncSummary:
    """同步摘要"""
    start_time: str
    end_time: str
    total_files: int
    success_count: int
    failed_count: int
    total_size: int
    results: List[Dict]


class COSSync:
    """COS同步器"""

    def __init__(
        self,
        bucket: Optional[str] = None,
        region: str = "ap-guangzhou",
    ):
        """
        初始化同步器

        Args:
            bucket: COS Bucket名称
            region: COS区域
        """
        self.bucket = bucket or os.getenv('COS_BUCKET', 'nemt-marketdata')
        self.region = region
        self._client = None

        # 从环境变量获取凭证
        self._secret_id = os.getenv('COS_SECRET_ID', '')
        self._secret_key = os.getenv('COS_SECRET_KEY', '')

    def _get_client(self):
        """获取COS客户端"""
        if self._client is None:
            try:
                from qcloud_cos import CosConfig, CosS3Client
            except ImportError:
                raise ImportError(
                    "cos-python-sdk-v5 is required. "
                    "Install with: pip install cos-python-sdk-v5"
                )

            if not self._secret_id or not self._secret_key:
                raise ValueError(
                    "COS credentials not found. "
                    "Set COS_SECRET_ID and COS_SECRET_KEY in environment "
                    "or cos_sync.env file."
                )

            config = CosConfig(
                Region=self.region,
                SecretId=self._secret_id,
                SecretKey=self._secret_key,
            )
            self._client = CosS3Client(config)

        return self._client

    def calculate_checksum(self, file_path: str) -> str:
        """计算文件MD5"""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()

    def sync_file(
        self,
        local_path: str,
        remote_path: str,
        dry_run: bool = False,
    ) -> SyncResult:
        """
        同步单个文件

        Args:
            local_path: 本地文件路径
            remote_path: COS远程路径
            dry_run: 是否为演练模式

        Returns:
            SyncResult
        """
        size = os.path.getsize(local_path)
        checksum = self.calculate_checksum(local_path)

        if dry_run:
            logger.info(f"[DRYRUN] Would upload: {local_path} -> {remote_path} ({size:,} bytes)")
            return SyncResult(
                local_path=local_path,
                remote_path=remote_path,
                success=True,
                size=size,
                checksum=checksum,
            )

        try:
            client = self._get_client()

            # 上传文件
            client.upload_file(
                Bucket=self.bucket,
                Key=remote_path,
                LocalFilePath=local_path,
            )

            logger.info(f"[OK] {local_path} -> cos://{self.bucket}/{remote_path}")
            return SyncResult(
                local_path=local_path,
                remote_path=remote_path,
                success=True,
                size=size,
                checksum=checksum,
            )

        except Exception as e:
            logger.error(f"[FAIL] {local_path}: {e}")
            return SyncResult(
                local_path=local_path,
                remote_path=remote_path,
                success=False,
                size=size,
                checksum=checksum,
                error=str(e),
            )

    def sync_directory(
        self,
        local_dir: str,
        remote_dir: str,
        pattern: str = "*.csv",
        dry_run: bool = False,
        max_workers: int = 10,
    ) -> List[SyncResult]:
        """
        同步整个目录

        Args:
            local_dir: 本地目录
            remote_dir: COS远程目录
            pattern: 文件匹配模式
            dry_run: 是否为演练模式
            max_workers: 并发数

        Returns:
            同步结果列表
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading

        local_path = Path(local_dir)
        if not local_path.exists():
            raise FileNotFoundError(f"Directory not found: {local_dir}")

        # 扫描文件
        files = list(local_path.glob(pattern))
        logger.info(f"Found {len(files)} files to sync")

        if not files:
            logger.warning("No files found matching pattern")
            return []

        # 移除远程目录末尾的斜杠
        remote_dir = remote_dir.rstrip('/')

        results = []
        counter_lock = threading.Lock()
        completed = 0

        def sync_task(file_path: Path) -> SyncResult:
            nonlocal completed
            rel_path = file_path.relative_to(local_path)
            remote_path = f"{remote_dir}/{rel_path}"

            result = self.sync_file(str(file_path), remote_path, dry_run)

            with counter_lock:
                completed += 1
                if completed % 100 == 0:
                    logger.info(f"Progress: {completed}/{len(files)}")

            return result

        # 并发上传
        if dry_run:
            for file_path in files:
                results.append(sync_task(file_path))
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(sync_task, f) for f in files]
                for future in as_completed(futures):
                    results.append(future.result())

        return results

    def list_remote(self, prefix: str = "") -> List[Dict]:
        """
        列出COS远程文件

        Args:
            prefix: 路径前缀

        Returns:
            文件列表
        """
        try:
            client = self._get_client()

            response = client.list_objects(
                Bucket=self.bucket,
                Prefix=prefix,
            )

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['Last-Modified'],
                })

            return files

        except Exception as e:
            logger.error(f"Failed to list remote: {e}")
            return []

    def delete_remote(self, remote_path: str) -> bool:
        """
        删除COS远程文件

        Args:
            remote_path: COS远程路径

        Returns:
            是否删除成功
        """
        try:
            client = self._get_client()
            client.delete_object(
                Bucket=self.bucket,
                Key=remote_path,
            )
            logger.info(f"[DELETED] cos://{self.bucket}/{remote_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return False

    def save_sync_report(self, results: List[SyncResult], output_path: str):
        """保存同步报告"""
        summary = SyncSummary(
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            total_files=len(results),
            success_count=sum(1 for r in results if r.success),
            failed_count=sum(1 for r in results if not r.success),
            total_size=sum(r.size for r in results),
            results=[{
                'local': r.local_path,
                'remote': r.remote_path,
                'success': r.success,
                'size': r.size,
                'error': r.error,
            } for r in results],
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_files': summary.total_files,
                'success_count': summary.success_count,
                'failed_count': summary.failed_count,
                'total_size': summary.total_size,
                'results': summary.results,
            }, f, indent=2)

        logger.info(f"Sync report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='COS Sync - 同步数据到腾讯云COS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 同步目录
  python sync_to_cos.py --local-dir ./data/us_stocks/daily --remote-dir us_stocks/daily

  # 演练模式（不实际同步）
  python sync_to_cos.py --local-dir ./data --remote-dir us_stocks --dry-run

  # 指定文件模式
  python sync_to_cos.py --local-dir ./data --remote-dir us_stocks --pattern "*.csv"

  # 增加并发数
  python sync_to_cos.py --local-dir ./data --remote-dir us_stocks --workers 20

  # 列出远程文件
  python sync_to_cos.py --list --prefix us_stocks/daily

Environment Variables:
  COS_SECRET_ID - COS Secret ID
  COS_SECRET_KEY - COS Secret Key
  COS_BUCKET - COS Bucket名称 (默认: nemt-marketdata)
        """
    )

    # 基本参数
    parser.add_argument('--local-dir', type=str, help='本地目录路径')
    parser.add_argument('--remote-dir', type=str, help='COS远程目录')
    parser.add_argument('--pattern', type=str, default='*.csv', help='文件匹配模式 (默认: *.csv)')

    # 选项
    parser.add_argument('--dry-run', action='store_true', help='演练模式，不实际同步')
    parser.add_argument('--workers', type=int, default=10, help='并发数 (默认: 10)')
    parser.add_argument('--report', type=str, help='保存同步报告的路径')

    # 查询操作
    parser.add_argument('--list', action='store_true', help='列出远程文件')
    parser.add_argument('--prefix', type=str, default='', help='列出指定前缀的文件')

    # COS配置
    parser.add_argument('--bucket', type=str, default='nemt-marketdata', help='COS Bucket')
    parser.add_argument('--region', type=str, default='ap-guangzhou', help='COS区域')

    args = parser.parse_args()

    # 创建同步器
    syncer = COSSync(bucket=args.bucket, region=args.region)

    # 检查凭证
    if not os.getenv('COS_SECRET_ID'):
        logger.warning("COS_SECRET_ID not set in environment")
    if not os.getenv('COS_SECRET_KEY'):
        logger.warning("COS_SECRET_KEY not set in environment")

    results = []

    if args.list:
        # 列出远程文件
        files = syncer.list_remote(args.prefix)
        print(f"\ncos://{args.bucket}/{args.prefix}")
        print("-" * 60)
        for f in files[:50]:
            size = f['size']
            s = f"{size/1024:.1f}KB" if size < 1048576 else f"{size/1048576:.1f}MB"
            print(f"  {s:>10}  {f['key']}")
        if len(files) > 50:
            print(f"  ... {len(files) - 50} more")
        print("-" * 60)
        print(f"Total: {len(files)} files")

    elif args.local_dir and args.remote_dir:
        # 执行同步
        results = syncer.sync_directory(
            args.local_dir,
            args.remote_dir,
            pattern=args.pattern,
            dry_run=args.dry_run,
            max_workers=args.workers,
        )

        # 打印摘要
        success = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        total_size = sum(r.size for r in results)

        print("\n" + "=" * 60)
        print("SYNC SUMMARY")
        print("=" * 60)
        print(f"Total files: {len(results)}")
        print(f"Success: {len(success)}")
        print(f"Failed: {len(failed)}")
        print(f"Total size: {total_size/1024/1024:.2f} MB")
        print("=" * 60)

        if failed:
            print("\nFailed files:")
            for r in failed:
                print(f"  - {r.local_path}: {r.error}")

        # 保存报告
        if args.report:
            syncer.save_sync_report(results, args.report)

    else:
        parser.print_help()
        print("\nError: 需要指定 --local-dir 和 --remote-dir, 或使用 --list")


if __name__ == '__main__':
    main()
