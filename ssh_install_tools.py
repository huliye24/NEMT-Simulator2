#!/usr/bin/env python3
"""
Install dev tools on cloud server
"""

import sys

try:
    import paramiko
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def run_cmd(client, cmd, password, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def main():
    host = "42.51.42.123"
    port = 22
    username = "root"
    password = "YrV27j15"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password, timeout=30)
    print("Connected!")
    
    commands = [
        ("Update packages", "apt update"),
        ("Install build tools", "apt install -y build-essential git curl wget"),
        ("Install Python pip", "apt install -y python3-pip python3-venv"),
        ("Install Node.js 20.x", "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt install -y nodejs"),
        ("Verify Node.js", "node --version"),
        ("Verify npm", "npm --version"),
        ("Install essential npm packages", "npm install -g typescript @vue/cli"),
        ("Install Python packages", "pip3 install numpy pandas scipy matplotlib jupyterlab"),
        ("Create workspace", "mkdir -p /root/nemt_workspace"),
    ]
    
    for name, cmd in commands:
        print(f"\nInstalling: {name}...")
        try:
            output, error = run_cmd(client, cmd, password, timeout=300)
            if error and "error" not in error.lower()[:100]:
                print(f"  Warning: {error[:200]}")
            print(f"  Done!")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Final verification
    print("\n" + "=" * 60)
    print("Final Verification:")
    print("=" * 60)
    
    verifications = [
        "node --version",
        "npm --version",
        "python3 --version",
        "pip3 --version",
        "git --version",
    ]
    
    for cmd in verifications:
        output, _ = run_cmd(client, cmd, password)
        print(f"  {output.strip()}")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    main()
