#!/usr/bin/env python3
"""
SSH Connect Script for NEMT Server
"""

import sys
import os
import time

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def ssh_connect(host, port, username, password):
    """Connect to SSH server and execute commands"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}:{port}...")
    client.connect(host, port=port, username=username, password=password, timeout=10)
    print("Connected successfully!")
    
    return client

def execute_command(client, command):
    """Execute command on remote server"""
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return output, error

def main():
    host = "42.51.42.123"
    port = 22
    username = "root"
    password = "YrV27j15"
    
    try:
        client = ssh_connect(host, port, username, password)
        
        # Run initial commands
        commands = [
            "echo '=== System Info ==='",
            "uname -a",
            "uptime",
            "echo ''",
            "echo '=== Disk Usage ==='",
            "df -h",
            "echo ''",
            "echo '=== Memory Usage ==='",
            "free -h",
            "echo ''",
            "echo '=== Python Version ==='",
            "python3 --version",
            "echo ''",
            "echo '=== Installed Packages ==='",
            "pip3 list 2>/dev/null | head -20 || echo 'pip not available'",
        ]
        
        for cmd in commands:
            output, error = execute_command(client, cmd)
            if output:
                print(output)
            if error:
                print(f"Error: {error}")
        
        client.close()
        print("\nSSH session closed.")
        
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check credentials.")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"SSH error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
