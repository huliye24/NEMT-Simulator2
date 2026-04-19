#!/usr/bin/env python3
"""Upload and run benchmark on remote server"""

import sys
import os
import paramiko
import json

def main():
    host = "42.51.42.123"
    port = 22
    username = "root"
    
    key_path = os.path.join(os.path.dirname(__file__), "ssh_key_nemt")
    
    print("Connecting to cloud server...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    private_key = paramiko.RSAKey.from_private_key_file(key_path)
    client.connect(host, port=port, username=username, pkey=private_key, timeout=30)
    
    # Upload benchmark script
    print("Uploading benchmark script...")
    with open("benchmark.py", "r") as f:
        benchmark_code = f.read()
    
    sftp = client.open_sftp()
    sftp.putfo(open("benchmark.py", "r"), "/root/benchmark.py")
    sftp.close()
    print("Uploaded!")
    
    # Run benchmark
    print("\nRunning benchmark on cloud server...")
    print("(This may take a few minutes...)\n")
    
    stdin, stdout, stderr = client.exec_command("cd /root && python3 benchmark.py", timeout=300)
    
    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line, end='')
    
    # Get results
    sftp = client.open_sftp()
    sftp.get("/root/benchmark_results.json", "benchmark_cloud_results.json")
    sftp.close()
    
    # Read cloud results
    with open("benchmark_cloud_results.json", "r") as f:
        cloud_results = json.load(f)
    
    print("\n" + "=" * 60)
    print("Cloud Benchmark Complete!")
    print("=" * 60)
    
    client.close()
    return cloud_results

if __name__ == "__main__":
    main()
