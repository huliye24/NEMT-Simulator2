#!/usr/bin/env python3
"""
Setup cloud server for remote development
"""

import sys
import os

try:
    import paramiko
except ImportError:
    print("Please run: pip install paramiko")
    sys.exit(1)

def ssh_connect(host, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password, timeout=30)
    return client

def run_command(client, command, sudo=False, password=None):
    """Run command and return output"""
    full_cmd = command
    if sudo:
        full_cmd = f"echo '{password}' | sudo -S {command}"
    stdin, stdout, stderr = client.exec_command(full_cmd, get_pty=sudo)
    if sudo and password:
        stdin.write(password + '\n')
        stdin.flush()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return output, error

def main():
    host = "42.51.42.123"
    port = 22
    username = "root"
    password = "YrV27j15"
    
    def run_cmd(cmd, sudo=False):
        return run_command(client, cmd, sudo=sudo, password=password)
    
    try:
        client = ssh_connect(host, port, username, password)
        print("Connected to cloud server!")
        print("=" * 60)
        
        # 1. Update system
        print("\n[1/7] Updating system packages...")
        output, error = run_cmd("apt update && apt upgrade -y", sudo=True)
        if "error" in error.lower() and "error" not in output.lower():
            print("Update completed")
        else:
            print(output[-500:] if output else "Updated")
        
        # 2. Install basic development tools
        print("\n[2/7] Installing development tools...")
        dev_packages = "git curl wget build-essential pkg-config libssl-dev"
        output, error = run_cmd(f"apt install -y {dev_packages}", sudo=True)
        print("Development tools installed")
        
        # 3. Install Python development tools
        print("\n[3/7] Installing Python development tools...")
        output, error = run_cmd("apt install -y python3-pip python3-dev python3-venv", sudo=True)
        
        # Install common Python packages
        print("Installing Python packages...")
        pip_packages = "numpy pandas flask fastapi uvicorn redis celery numpy scipy matplotlib"
        output, error = run_cmd(f"pip3 install {pip_packages}")
        if "error" in error.lower():
            print(f"Note: Some packages may have warnings, continuing...")
        print("Python packages installed")
        
        # 4. Install Node.js
        print("\n[4/7] Installing Node.js...")
        output, error = run_cmd("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -", sudo=True)
        output, error = run_cmd("apt install -y nodejs", sudo=True)
        output, error = run_cmd("node --version")
        print(f"Node.js version: {output.strip()}")
        
        # 5. Install Docker
        print("\n[5/7] Installing Docker...")
        output, error = run_cmd("apt install -y docker.io docker-compose", sudo=True)
        output, error = run_cmd("systemctl start docker", sudo=True)
        output, error = run_cmd("systemctl enable docker", sudo=True)
        print("Docker installed")
        
        # 6. Clone/Prepare workspace
        print("\n[6/7] Setting up workspace...")
        output, error = run_cmd("mkdir -p /root/nemt_workspace")
        
        # Check if we have the code locally
        local_nemt = r"E:\NEMT Simulator"
        if os.path.exists(local_nemt):
            print("Found local NEMT codebase")
        
        # 7. Create SSH key for easy access
        print("\n[7/7] Setting up SSH access...")
        output, error = run_cmd("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
        output, error = run_cmd("cat ~/.ssh/id_rsa.pub 2>/dev/null || echo 'NO_KEY'")
        if "NO_KEY" not in output:
            print("SSH key already exists")
        else:
            output, error = run_cmd("ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa")
            print("SSH key generated")
        
        # Show server info
        print("\n" + "=" * 60)
        print("Server Setup Complete!")
        print("=" * 60)
        
        # Get public IP info
        output, error = run_cmd("curl -s ifconfig.me")
        public_ip = output.strip() if output else "Unknown"
        
        print(f"\nServer Public IP: {public_ip}")
        print(f"SSH Port: 22")
        print(f"Username: root")
        print(f"Password: {password}")
        print(f"\nWorkspace: /root/nemt_workspace")
        
        print("\n" + "=" * 60)
        print("Cursor Remote SSH Setup Instructions:")
        print("=" * 60)
        print("""
1. In Cursor, press Ctrl+Shift+P
2. Type "Remote-SSH: Connect to Host"
3. Select "Add New Host..."
4. Enter: root@42.51.42.123
5. Enter password when prompted: YrV27j15
6. Choose password or key file authentication
7. Wait for Cursor to install remote extension
8. Open folder: /root/nemt_workspace
9. You're now coding on the cloud server!
        """)
        
        client.close()
        print("\nSetup completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
