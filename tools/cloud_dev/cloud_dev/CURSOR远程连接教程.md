# Cursor 远程连接云端教程

## 方法A：最简单 - 一键连接（推荐）

### 步骤1：安装Remote SSH扩展

1. 在Cursor中按 `Ctrl+Shift+X`
2. 搜索 "Remote SSH"
3. 安装 **Remote - SSH**（Microsoft）

### 步骤2：连接

1. 按 `Ctrl+Shift+P`，输入 `Remote-SSH: Connect to Host`
2. 选择 **+ Add New Host**
3. 输入：`root@42.51.42.123`
4. 输入密码：`YrV27j15`

### 步骤3：选择文件夹

连接后按 `Ctrl+K Ctrl+O`，输入 `/root` 回车

---

## 方法B：使用SSH密钥（更安全）

### 步骤1：生成SSH密钥

在PowerShell中运行：

```powershell
ssh-keygen -t rsa -b 4096 -C "nemt-cloud"
```

一路回车，密钥保存在 `C:\Users\Administrator\.ssh\`

### 步骤2：上传公钥到云端

```powershell
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh root@42.51.42.123 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 步骤3：配置SSH config

创建文件 `C:\Users\Administrator\.ssh\config`（用记事本）：

```
Host nemt
    HostName 42.51.42.123
    User root
    Port 22
    IdentityFile C:\Users\Administrator\.ssh\id_rsa
```

### 步骤4：在Cursor中连接

`Ctrl+Shift+P` → `Remote-SSH: Connect to Host` → 选择 `nemt`

---

## 连接后的界面

```
┌─────────────────────────────────────────────────────┐
│  root@42.51.42.123:~                [SSH] [+] [⚙]  │
├─────────────────────────────────────────────────────┤
│  📁 文件浏览器              │  📝 编辑器             │
│  └─ /root                  │  └─ main.py           │
│     ├─ ai.py              │     │                  │
│     ├─ code.py            │     │                  │
│     ├─ nemt-workspace     │     │                  │
│     └─ ...                │     │                  │
├─────────────────────────────────────────────────────┤
│  终端 (云端)                                    [+] │
│  root@server:~#                                   │
└─────────────────────────────────────────────────────┘
```

## 快捷操作

| 操作 | 快捷键 |
|------|--------|
| 新建文件 | `Ctrl+N` |
| 保存 | `Ctrl+S` |
| 打开终端 | `Ctrl+`` |
| 命令面板 | `Ctrl+Shift+P` |
| AI助手 | `Ctrl+L` |

---

## 常见问题

### Q: 连接超时？
检查网络，确保22端口开放

### Q: 密码输入多次？
推荐使用方法B（SSH密钥），只需输入一次

### Q: 如何打开前端项目？
连接后在文件浏览器中导航到 `/root/nemt-workspace/web`

---

## 优势对比

| | 本地Cursor | Cursor连接云端 |
|--|-----------|--------------|
| 代码存储 | 本地 | 云端 |
| AI助手 | ✅ | ✅ |
| 运行代码 | 本地 | 云端8核CPU |
| 断电丢失 | 会 | 不会 |
| 需要网络 | 不需要 | 需要 |
