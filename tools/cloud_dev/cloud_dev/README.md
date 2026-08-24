# 云端开发环境 (Cloud Dev Environment)

基于轻量级Web IDE **wede** 实现的远程编程环境，代码在云端运行，本地只需浏览器访问。

## 快速开始

### 访问地址
- **URL**: http://42.51.42.123:3000
- **密码**: NEMT2026

### 管理命令

```bash
# 查看状态
python cloud_dev.py status

# 启动服务
python cloud_dev.py start

# 停止服务
python cloud_dev.py stop

# 重启服务
python cloud_dev.py restart

# 查看日志
python cloud_dev.py logs

# 查看更多日志
python cloud_dev.py logs 50

# 重新初始化配置
python cloud_dev.py setup
```

Windows 用户也可以使用批处理文件:
```bat
cloud_dev.bat status
cloud_dev.bat start
cloud_dev.bat stop
```

## 功能特性

- **代码编辑器**: 支持多种编程语言的语法高亮
- **Web终端**: 直接在浏览器中使用Linux命令
- **Git客户端**: 可视化版本控制
- **文件浏览器**: 管理项目文件

## 工作原理

```
┌─────────────┐     HTTP      ┌─────────────────┐
│   浏览器    │ ◄──────────► │  云服务器        │
│             │              │  ┌───────────┐  │
│  访问页面   │              │  │   wede    │  │
│  编辑代码   │              │  │  10MB     │  │
│  提交Git   │              │  │           │  │
│             │              │  │  Python   │  │
│             │              │  │  Node.js  │  │
│             │              │  │  Go       │  │
│             │              │  └───────────┘  │
└─────────────┘              └─────────────────┘
```

## 优势

1. **零配置**: 无需在本地安装任何开发工具
2. **跨平台**: 任何设备只要有浏览器就能编程
3. **资源丰富**: 使用云服务器的计算资源
4. **数据安全**: 代码存储在云端，不易丢失
5. **协作方便**: 轻松分享屏幕和代码

## 故障排除

### 服务无法启动
```bash
python cloud_dev.py logs
```

### 端口未监听
```bash
python cloud_dev.py restart
```

### 需要重置配置
```bash
python cloud_dev.py setup
```

## 技术栈

- **wede**: 轻量级自托管Web IDE (~10MB)
- **systemd**: 服务管理
- **ufw**: 防火墙配置
