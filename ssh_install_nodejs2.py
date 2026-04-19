#!/usr/bin/env python3
"""Wait for apt to finish and install Node.js"""

import sys
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("42.51.42.123", port=22, username="root", password="YrV27j15", timeout=30)
    
    print("Waiting for other apt processes to finish...")
    
    # Wait for apt to be available
    for i in range(60):  # Wait up to 60 seconds
        stdin, stdout, stderr = client.exec_command("pgrep -x apt || echo 'apt_not_running'")
        stdout.channel.recv_exit_status()
        result = stdout.read().decode().strip()
        
        if result == "apt_not_running":
            print("apt is free, continuing...")
            break
        print(f"Waiting... ({i+1}/60)")
        time.sleep(1)
    
    # Now install Node.js
    print("\nInstalling Node.js...")
    
    stdin, stdout, stderr = client.exec_command("apt install -y nodejs npm", timeout=300)
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if error:
        print(f"Error: {error[:500]}")
    
    # Verify
    stdin, stdout, stderr = client.exec_command("node --version")
    stdout.channel.recv_exit_status()
    node_version = stdout.read().decode().strip()
    
    stdin, stdout, stderr = client.exec_command("npm --version")
    stdout.channel.recv_exit_status()
    npm_version = stdout.read().decode().strip()
    
    print(f"\nNode.js: {node_version}")
    print(f"npm: {npm_version}")
    
    if node_version:
        print("\nNode.js installed successfully!")
    else:
        print("\nInstallation may have failed, checking...")
        stdin, stdout, stderr = client.exec_command("which node")
        stdout.channel.recv_exit_status()
        print(f"node location: {stdout.read().decode().strip()}")
    
    client.close()

if __name__ == "__main__":
    main()
