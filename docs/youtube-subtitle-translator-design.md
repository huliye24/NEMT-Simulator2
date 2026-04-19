# YouTube 智能字幕翻译器 技术方案

## 一、项目概述

### 1.1 项目背景

随着全球化的深入发展，YouTube 已成为最重要的视频学习平台之一。然而，语言障碍限制了用户对优质外语视频内容的获取。本项目旨在构建一个实时的 YouTube 字幕翻译工具，帮助用户无障碍观看外语视频。

### 1.2 核心功能

- 实时捕获 YouTube 视频字幕
- 调用 DeepSeek API 进行高质量翻译
- 双行显示：上方英文原文，下方中文翻译
- 支持拖动定位，位置自动保存
- 多种目标语言支持（中文、日语、韩语）
- 本地缓存机制，避免重复翻译

## 二、技术框架

### 2.1 架构选择

```
┌─────────────────────────────────────────────────────────────┐
│                     YouTube 页面环境                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  浮动按钮   │  │  通知栏     │  │   字幕翻译层         │ │
│  │  (FAB)     │  │ (Top Bar)   │  │  (绝对定位在播放器内) │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Greasemonkey/Tampermonkey 运行环境       │
│                   (Tampermonkey UserScript)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │    DeepSeek API     │
                   │   (外部翻译服务)     │
                   └─────────────────────┘
```

### 2.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 运行环境 | Tampermonkey 4.0+ | 用户脚本管理器，支持油猴扩展 |
| 脚本语言 | JavaScript (ES6+) | 原生支持，无需构建 |
| 样式方案 | 内联 CSS + `!important` | 优先级控制，应对 YouTube 样式覆盖 |
| 存储方案 | GM_storage API | Tampermonkey 原生 API，数据持久化 |
| 网络请求 | GM_xmlhttpRequest | 跨域请求封装 |
| 翻译服务 | DeepSeek Chat API | 高质量、低成本的翻译服务 |

## 三、核心模块设计

### 3.1 模块架构

```
youtube-subtitle-translator.user.js
├── 配置管理模块
│   ├── getApiKey()        # 读取 API Key
│   ├── isEnabled()         # 读取启用状态
│   └── GM_setValue()       # 持久化配置
│
├── UI 组件模块
│   ├── createFloatingButton()    # 浮动操作按钮
│   ├── createNotificationBar()   # 顶部状态栏
│   ├── createSubtitleContainer() # 字幕容器（注入播放器）
│   └── showSettings()            # 设置面板
│
├── 翻译功能模块
│   ├── processSubtitles()        # 字幕处理入口
│   ├── translate()              # 翻译协调器
│   ├── callAPI()               # DeepSeek API 调用
│   └── showSubtitle()          # 字幕渲染
│
├── 拖动系统模块
│   ├── initSubtitleDrag()      # 初始化拖动
│   ├── startDrag()            # 开始拖动
│   ├── doDrag()              # 拖动中
│   ├── endDrag()             # 结束拖动
│   └── updatePosition()       # 位置更新
│
└── 初始化模块
    ├── init()                  # 主初始化
    └── tryCreateSubtitle()     # 字幕容器创建器
```

### 3.2 数据流

```
视频播放
    │
    ▼
字幕元素出现 (.ytp-caption-segment)
    │
    ▼
processSubtitles() [timeupdate 事件]
    │
    ├──▶ 缓存命中 ──────▶ showSubtitle()
    │
    └──▶ 缓存未命中
            │
            ▼
        限流检查 (400ms 间隔)
            │
            ▼
        callAPI() ──────▶ DeepSeek API
                              │
                              ▼
                         缓存存储
                              │
                              ▼
                         showSubtitle()
```

## 四、关键技术方案

### 4.1 字幕定位方案

**问题**：YouTube 页面布局复杂，响应式设计导致视频播放器位置不固定。

**方案**：将字幕容器注入到视频播放器内部，使用 `position: absolute` 相对定位。

```javascript
// 注入到播放器内部
const player = document.querySelector('#movie_player');
player.appendChild(container);

// 使用绝对定位，相对于播放器定位
container.style.cssText = `
    position: absolute !important;
    left: 50% !important;
    bottom: 50px !important;
    transform: translateX(-50%) !important;
    z-index: 2147483647 !important;
`;
```

**优势**：
- 自动跟随视频播放器位置
- 不受页面其他元素影响
- 位置计算基于播放器而非视口

### 4.2 拖动定位方案

**方案**：使用偏移量（offset）而非绝对像素坐标。

```javascript
// 存储结构
{
    bottom: 50,  // 底部偏移
    left: 0      // 水平偏移
}

// 位置更新
function updatePosition() {
    if (offsetLeft === 0) {
        container.style.setProperty('left', '50%', 'important');
        container.style.setProperty('transform', 'translateX(-50%)', 'important');
    } else {
        container.style.setProperty('left', `calc(50% + ${offsetLeft}px)`, 'important');
        container.style.setProperty('transform', 'none', 'important');
    }
    container.style.setProperty('bottom', offsetBottom + 'px', 'important');
}
```

**优势**：
- 不受页面缩放影响
- 相对定位更稳定
- 存储数据量小

### 4.3 样式优先级方案

**问题**：YouTube 使用大量 `!important` 样式，用户脚本难以覆盖。

**方案**：双重 `!important` + `setProperty` 方法。

```javascript
// 方案 1：内联样式 + !important
element.style.cssText = `
    display: block !important;
    z-index: 2147483647 !important;
`;

// 方案 2：setProperty 方法
element.style.setProperty('display', 'block', 'important');

// 方案 3：GM_addStyle 注入全局样式
GM_addStyle(`
    #nempt-subtitle { display: block !important; }
`);
```

### 4.4 翻译缓存方案

```javascript
const cache = new Map();

// 缓存键值
cache.has(text);           // 检查缓存
cache.get(text);           // 获取缓存
cache.set(text, result);   // 存储缓存
```

**容量管理**：原生 Map 无限制，实际使用中字幕内容有限，缓存自然收敛。

### 4.5 限流方案

```javascript
let lastTranslateTime = 0;

async function translate(text) {
    const now = Date.now();
    if (now - lastTranslateTime < 400) {
        await new Promise(r => setTimeout(r, 400 - (now - lastTranslateTime)));
    }
    lastTranslateTime = Date.now();
    // 调用 API...
}
```

**原因**：
- 防止 API 调用过于频繁
- 字幕更新频率约 1-3 秒
- 400ms 间隔可捕获大部分变化

### 4.6 事件监听防重复

```javascript
function watchVideo() {
    const video = document.querySelector('video');
    if (!video) return;
    
    // 防止重复添加监听器
    if (video.dataset.nemptRegistered) return;
    video.dataset.nemptRegistered = 'true';
    
    video.addEventListener('timeupdate', processSubtitles);
}

// 初始检查
watchVideo();

// MutationObserver 监听动态加载
const observer = new MutationObserver(watchVideo);
observer.observe(document.body, { childList: true, subtree: true });
```

## 五、API 对接

### 5.1 DeepSeek API 配置

```javascript
const API_URL = 'https://api.deepseek.com/chat/completions';

GM_xmlhttpRequest({
    method: 'POST',
    url: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
    },
    data: JSON.stringify({
        model: 'deepseek-chat',
        messages: [{
            role: 'user',
            content: `翻译成${targetLang}，只返回翻译：\n\n${text}`
        }],
        temperature: 0.3,    // 低随机性，保持翻译一致性
        max_tokens: 500    # 限制单次翻译长度
    })
});
```

### 5.2 提示词设计

```
翻译成中文，只返回翻译：

[字幕内容]
```

**设计考量**：
- 简洁明确，减少 token 消耗
- `temperature: 0.3` 保持翻译一致性
- `max_tokens: 500` 防止过长回复

## 六、用户界面

### 6.1 组件清单

| 组件 | 描述 | 层级 |
|------|------|------|
| 浮动按钮 (FAB) | 右下角圆形按钮，点击打开设置 | z-index: 99999 |
| 通知栏 | 顶部状态栏，显示配置状态 | z-index: 99999 |
| 字幕容器 | 视频内字幕显示 | z-index: 2147483647 |
| 设置面板 | 模态框，配置各项参数 | z-index: 100001 |
| Toast | 临时提示，3秒自动消失 | z-index: 100002 |

### 6.2 字幕双行显示

```
┌─────────────────────────────┐
│  英文原文 (灰色, 18px)      │  ← 可拖动区域
│  中文翻译 (白色, 22px)      │
└─────────────────────────────┘
```

## 七、数据存储

### 7.1 存储键值

| 键名 | 类型 | 说明 |
|------|------|------|
| `deepseek_api_key` | string | DeepSeek API Key |
| `target_lang` | string | 目标语言 (zh/ja/ko) |
| `is_enabled` | boolean | 翻译功能开关 |
| `subtitle_position` | string | 位置预设 (top/bottom/center/custom) |
| `subtitle_offset` | object | 自定义偏移 {bottom, left} |

### 7.2 存储 API

```javascript
// 读取
GM_getValue('key', defaultValue);

// 写入
GM_setValue('key', value);
```

## 八、浏览器兼容

### 8.1 支持环境

| 环境 | 最低版本 |
|------|----------|
| Tampermonkey | 4.0+ |
| Chrome | 66+ |
| Firefox | 61+ |
| Edge | 79+ |
| Safari | 11.1+ |

### 8.2 API 支持情况

- `GM_xmlhttpRequest` ✅
- `GM_setValue` / `GM_getValue` ✅
- `GM_addStyle` ✅
- `GM_log` ✅

## 九、部署方式

### 9.1 安装步骤

1. 安装 Tampermonkey 浏览器扩展
2. 点击 Tampermonkey 图标 → 创建新脚本
3. 粘贴代码并保存
4. 访问 YouTube 视频页面
5. 配置 DeepSeek API Key

### 9.2 权限说明

```javascript
// @grant GM_xmlhttpRequest  - 跨域请求
// @grant GM_setValue       - 数据存储
// @grant GM_getValue       - 数据读取
// @grant GM_addStyle       - 样式注入
// @grant GM_log            - 日志输出
// @connect api.deepseek.com - 连接白名单
```

## 十、版本演进

### 10.1 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | - | 初始版本，基础翻译功能 |
| 2.0.0 | - | 重构定位系统，修复样式冲突 |
| 2.1.0 | - | 双行字幕显示，拖动功能 |

### 10.2 未来规划

- [ ] 多语言字幕同时显示
- [ ] 快捷键自定义
- [ ] 翻译历史记录
- [ ] 导出字幕功能
- [ ] YouTube Shorts 支持

## 十一、故障排查

### 11.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 字幕不显示 | 未开启 YouTube 字幕 | 视频设置中启用 CC |
| 翻译无响应 | API Key 未配置 | 点击浮动按钮配置 |
| 位置错乱 | 缓存的位置数据过期 | 设置中点击"重置位置" |
| 拖动无效 | 脚本未更新 | 刷新脚本或重新安装 |

### 11.2 调试方法

1. 打开浏览器开发者工具 (F12)
2. Tampermonkey 面板查看脚本日志
3. 控制台搜索 `nempt` 或 `YouTube翻译器`

## 十二、附录

### 12.1 文件结构

```
youtube-subtitle-translator.user.js   # 主脚本文件
├── 元数据 (Userscript Header)
├── 配置管理
├── UI 组件
├── 翻译功能
├── 拖动系统
└── 初始化入口
```

### 12.2 参考资料

- [Tampermonkey Documentation](https://tampermonkey.net/documentation.php)
- [DeepSeek API Docs](https://platform.deepseek.com/docs)
- [YouTube Player API](https://developers.google.com/youtube/player_parameters)
