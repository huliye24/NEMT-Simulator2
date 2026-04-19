#!/usr/bin/env python3
"""Force kill apt and install Node.js"""

import sys
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("42.51.42.123", port=22, username="root", password="YrV27j15", timeout=30)
    
    print("Checking for running apt processes...")
    
    # Kill apt processes
    stdin, stdout, stderr = client.exec_command("pkill -9 apt; pkill -9 dpkg; sleep 2")
    stdout.channel.recv_exit_status()
    
    # Remove locks
    stdin, stdout, stderr = client.exec_command("rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock")
    stdout.channel.recv_exit_status()
    print("Removed apt locks")
    
    # Reconfigure dpkg
    stdin, stdout, stderr = client.exec_command("dpkg --configure -a", timeout=60)
    stdout.channel.recv_exit_status()
    
    time.sleep(2)
    
    # Now install Node.js
    print("\nInstalling Node.js...")
    
    stdin, stdout, stderr = client.exec_command("apt update && apt install -y nodejs npm", timeout=300)
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if "error" in error.lower():
        print(f"Note: {error[:200]}")
    
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
        print("\nNode.js not found, trying alternative install...")
        # Try nvm install
        stdin, stdout, stderr = client.exec_command("curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash", timeout=120)
        stdout.channel.recv_exit_status()
        
        stdin, stdout, stderr = client.exec_command("source ~/.bashrc && nvm install 20")
        stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        
        stdin, stdout, stderr = client.exec_command("source ~/.bashrc && node --version")
        stdout.channel.recv_exit_status()
        node_version = stdout.read().decode().strip()
        print(f"\nNode.js via nvm: {node_version}")
    
    client.close()

if __name__ == "__main__":
    main()
