#!/usr/bin/env python3
"""
Quick SSH Test - Check server status
"""

import sys

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def main():
    host = "42.51.42.123"
    port = 22
    username = "root"
    password = "YrV27j15"
    
    try:
        print(f"Connecting to {host}...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password, timeout=10)
        print("Connected!")
        print("=" * 60)
        
        # Quick system check
        commands = [
            ("System", "uname -a"),
            ("Uptime", "uptime"),
            ("CPU Cores", "nproc"),
            ("Memory", "free -h | grep Mem"),
            ("Disk", "df -h / | tail -1"),
            ("Python", "python3 --version"),
            ("Node", "node --version 2>/dev/null || echo 'Not installed'"),
            ("Docker", "docker --version 2>/dev/null || echo 'Not installed'"),
            ("Git", "git --version"),
            ("IP Address", "hostname -I"),
        ]
        
        for name, cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            if output:
                print(f"{name}: {output}")
            elif error:
                print(f"{name}: {error}")
        
        client.close()
        print("=" * 60)
        print("\nSetup is ready!")
        print("\nNext steps to use Cursor Remote SSH:")
        print("=" * 60)
        print("""
1. In Cursor Desktop:
   - Press Ctrl+Shift+P
   - Type: Remote-SSH: Connect to Host
   - Select: Add New Host
   - Enter: root@42.51.42.123
   - Password: YrV27j15

2. Wait for Cursor to install VSCode Server on remote

3. Open folder: /root/nemt_workspace

4. You're now coding on the cloud server!
   - All processing happens on the cloud
   - Your local machine just displays the UI
   - Much faster for large codebases!
        """)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
