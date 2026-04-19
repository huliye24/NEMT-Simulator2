#!/usr/bin/env python3
"""Generate SSH key pair and upload to server"""

import sys
import os
import paramiko

def generate_ssh_key():
    """Generate SSH key pair"""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        print("Installing cryptography...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
    
    # Generate key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    
    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_ssh = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    
    # Save keys
    key_dir = os.path.dirname(os.path.abspath(__file__))
    private_key_path = os.path.join(key_dir, "ssh_key_nemt")
    public_key_path = private_key_path + ".pub"
    
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    os.chmod(private_key_path, 0o600)
    
    with open(public_key_path, 'wb') as f:
        f.write(public_ssh)
    
    print(f"Private key saved: {private_key_path}")
    print(f"Public key saved: {public_key_path}")
    
    return public_ssh.decode()

def upload_key_to_server(public_key):
    """Upload public key to server"""
    host = "42.51.42.123"
    port = 22
    username = "root"
    password = "YrV27j15"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password, timeout=30)
    
    print("Connected to server")
    
    # Create .ssh directory
    commands = [
        "mkdir -p ~/.ssh",
        "chmod 700 ~/.ssh",
    ]
    
    for cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
    
    # Add public key to authorized_keys
    cmd = f'echo "{public_key.strip()}" >> ~/.ssh/authorized_keys'
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    
    # Set permissions
    stdin, stdout, stderr = client.exec_command("chmod 600 ~/.ssh/authorized_keys")
    stdout.channel.recv_exit_status()
    
    print("Public key uploaded to server")
    
    # Verify
    stdin, stdout, stderr = client.exec_command("cat ~/.ssh/authorized_keys")
    stdout.channel.recv_exit_status()
    content = stdout.read().decode()
    print(f"authorized_keys contains {len(content.strip().split())} keys")
    
    client.close()
    
    return True

def test_passwordless_login():
    """Test passwordless login"""
    host = "42.51.42.123"
    port = 22
    username = "root"
    
    key_dir = os.path.dirname(os.path.abspath(__file__))
    private_key_path = os.path.join(key_dir, "ssh_key_nemt")
    
    print("\nTesting passwordless login...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Try with private key
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        
        stdin, stdout, stderr = client.exec_command("echo 'Passwordless login works!'")
        stdout.channel.recv_exit_status()
        result = stdout.read().decode().strip()
        
        print(f"Success: {result}")
        client.close()
        return True
        
    except Exception as e:
        print(f"Passwordless login failed: {e}")
        return False

def main():
    print("=" * 60)
    print("SSH Key Setup for Passwordless Login")
    print("=" * 60)
    
    # Generate key
    print("\n[1/3] Generating SSH key pair...")
    public_key = generate_ssh_key()
    print("Key generated successfully!")
    
    # Upload to server
    print("\n[2/3] Uploading public key to server...")
    upload_key_to_server(public_key)
    print("Public key uploaded!")
    
    # Test login
    print("\n[3/3] Testing passwordless login...")
    success = test_passwordless_login()
    
    if success:
        print("\n" + "=" * 60)
        print("SSH Passwordless Login Configured!")
        print("=" * 60)
        print("""
You can now connect without password:
  ssh -i ssh_key_nemt root@42.51.42.123

In Cursor:
1. Press Ctrl+Shift+P
2. Type "Remote-SSH: Open Configuration File"
3. Add host:
   Host nemt-cloud
     HostName 42.51.42.123
     User root
     IdentityFile e:\\NEMT Simulator\\ssh_key_nemt

4. Then connect with:
   Ctrl+Shift+P -> "Remote-SSH: Connect to Host" -> "nemt-cloud"
        """)
    else:
        print("\nPasswordless login setup failed. Please try again.")

if __name__ == "__main__":
    main()
