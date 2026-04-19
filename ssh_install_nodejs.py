#!/usr/bin/env python3
"""Quick Node.js installer"""

import sys
import paramiko

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("42.51.42.123", port=22, username="root", password="YrV27j15", timeout=30)
    
    print("Installing Node.js 20.x...")
    
    # Simple install
    cmds = [
        "apt update",
        "apt install -y nodejs npm",
    ]
    
    for cmd in cmds:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=180)
        stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        if output:
            print(output[-300:] if len(output) > 300 else output)
    
    # Verify
    stdin, stdout, stderr = client.exec_command("node --version")
    stdout.channel.recv_exit_status()
    node_version = stdout.read().decode().strip()
    
    stdin, stdout, stderr = client.exec_command("npm --version")
    stdout.channel.recv_exit_status()
    npm_version = stdout.read().decode().strip()
    
    print(f"\nNode.js: {node_version}")
    print(f"npm: {npm_version}")
    
    client.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
