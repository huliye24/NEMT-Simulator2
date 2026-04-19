// ==UserScript==
// @name         YouTube 智能字幕翻译器 v2
// @namespace    http://tampermonkey.net/
// @version      2.1.0
// @description  YouTube实时字幕翻译，支持DeepSeek API翻译为中文
// @author       NEMT
// @match        *://www.youtube.com/*
// @match        *://youtube.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_addStyle
// @grant        GM_log
// @connect      api.deepseek.com
// @run-at       document-end
// @license      MIT
// ==/UserScript==

(function() {
    'use strict';

    GM_log('[YouTube翻译器] 脚本开始加载...');

    // 状态读取（函数形式，实时获取最新设置）
    function getApiKey() { return GM_getValue('deepseek_api_key', ''); }
    function isEnabled() { return GM_getValue('is_enabled', true); }

    // 强制创建浮动按钮和通知
    function createFloatingButton() {
        const existing = document.getElementById('nempt-fab');
        if (existing) existing.remove();

        const fab = document.createElement('div');
        fab.id = 'nempt-fab';
        fab.innerHTML = '译';
        fab.style.cssText = `
            position: fixed !important;
            bottom: 100px !important;
            right: 24px !important;
            width: 56px !important;
            height: 56px !important;
            background: linear-gradient(135deg, #4a9eff, #0066ff) !important;
            border-radius: 50% !important;
            color: #fff !important;
            font-size: 20px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            z-index: 99999 !important;
            box-shadow: 0 6px 30px rgba(74, 158, 255, 0.5) !important;
            font-family: 'Microsoft YaHei', sans-serif !important;
            pointer-events: auto !important;
        `;

        if (!getApiKey()) {
            fab.style.animation = 'nempt-pulse 2s infinite';
            fab.title = '点击配置API Key';
        } else {
            fab.title = 'YouTube字幕翻译器 - 已配置';
        }

        document.body.appendChild(fab);
        GM_log('[YouTube翻译器] 浮动按钮已创建');

        fab.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            GM_log('[YouTube翻译器] 点击了浮动按钮');
            if (!getApiKey()) {
                showWelcome();
            } else {
                showSettings();
            }
        });
    }

    // 创建顶部通知栏
    function createNotificationBar() {
        const existing = document.getElementById('nempt-notification');
        if (existing) existing.remove();

        const bar = document.createElement('div');
        bar.id = 'nempt-notification';
        bar.innerHTML = `
            <span>YouTube 智能字幕翻译器</span>
            <span style="margin-left: 20px; color: ${getApiKey() ? '#4CAF50' : '#FF9800'}">
                ${getApiKey() ? '✓ 已配置API Key' : '⚠ 请先配置API Key'}
            </span>
            <button id="nempt-open-settings" style="
                margin-left: 20px;
                padding: 8px 16px;
                background: linear-gradient(135deg, #4a9eff, #0066ff);
                border: none;
                border-radius: 6px;
                color: #fff;
                cursor: pointer;
                font-size: 13px;
            ">${getApiKey() ? '设置' : '立即配置'}</button>
            <button id="nempt-close-notification" style="
                margin-left: 10px;
                padding: 8px 12px;
                background: rgba(255,255,255,0.1);
                border: none;
                border-radius: 6px;
                color: #999;
                cursor: pointer;
                font-size: 13px;
            ">关闭</button>
        `;

        bar.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            background: linear-gradient(135deg, #1a1a2e, #16213e) !important;
            color: #fff !important;
            padding: 12px 20px !important;
            display: flex !important;
            align-items: center !important;
            z-index: 99999 !important;
            font-family: 'Microsoft YaHei', sans-serif !important;
            font-size: 14px !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3) !important;
            box-sizing: border-box !important;
        `;

        document.body.appendChild(bar);
        document.body.style.paddingTop = '50px';

        document.getElementById('nempt-open-settings').addEventListener('click', () => {
            if (!getApiKey()) {
                showWelcome();
            } else {
                showSettings();
            }
        });

        document.getElementById('nempt-close-notification').addEventListener('click', () => {
            bar.style.display = 'none';
            document.body.style.paddingTop = '0';
        });

        GM_log('[YouTube翻译器] 通知栏已创建');
    }

    // 欢迎界面
    function showWelcome() {
        const overlay = document.createElement('div');
        overlay.id = 'nempt-welcome-overlay';
        overlay.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            background: rgba(0, 0, 0, 0.9) !important;
            z-index: 100000 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: 'Microsoft YaHei', sans-serif !important;
        `;

        overlay.innerHTML = `
            <div style="
                background: linear-gradient(145deg, #1a1a2e, #16213e);
                border-radius: 20px;
                padding: 40px;
                max-width: 450px;
                width: 90%;
                box-shadow: 0 25px 80px rgba(0,0,0,0.5);
            ">
                <h2 style="
                    color: #fff;
                    text-align: center;
                    margin: 0 0 10px 0;
                    font-size: 24px;
                ">YouTube 智能字幕翻译器</h2>
                <p style="color: #888; text-align: center; margin-bottom: 30px;">
                    实时翻译字幕为中文，支持DeepSeek高质量翻译
                </p>

                <div style="margin-bottom: 20px;">
                    <label style="color: #ccc; display: block; margin-bottom: 8px;">DeepSeek API Key</label>
                    <input type="password" id="nempt-api-key-input" placeholder="sk-xxxxxxxxxxxxxxxx"
                        style="
                            width: 100%;
                            padding: 14px;
                            background: rgba(0,0,0,0.4);
                            border: 2px solid rgba(255,255,255,0.1);
                            border-radius: 10px;
                            color: #fff;
                            font-size: 14px;
                            box-sizing: border-box;
                        ">
                    <small style="color: #666; font-size: 12px; margin-top: 6px; display: block;">
                        从 <a href="https://platform.deepseek.com/" target="_blank" style="color: #4a9eff;">DeepSeek开放平台</a> 获取
                    </small>
                </div>

                <div style="margin-bottom: 25px;">
                    <label style="color: #ccc; display: block; margin-bottom: 8px;">目标语言</label>
                    <select id="nempt-lang-select" style="
                        width: 100%;
                        padding: 12px;
                        background: rgba(0,0,0,0.4);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 10px;
                        color: #fff;
                        font-size: 14px;
                    ">
                        <option value="zh">中文</option>
                        <option value="ja">日语</option>
                        <option value="ko">韩语</option>
                    </select>
                </div>

                <button id="nempt-start-btn" style="
                    width: 100%;
                    padding: 14px;
                    background: linear-gradient(135deg, #4a9eff, #0066ff);
                    border: none;
                    border-radius: 10px;
                    color: #fff;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                ">开始使用</button>

                <button id="nempt-skip-btn" style="
                    width: 100%;
                    margin-top: 10px;
                    padding: 12px;
                    background: transparent;
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 10px;
                    color: #888;
                    font-size: 14px;
                    cursor: pointer;
                ">稍后再说</button>
            </div>
        `;

        document.body.appendChild(overlay);
        GM_log('[YouTube翻译器] 欢迎界面已显示');

        document.getElementById('nempt-start-btn').addEventListener('click', () => {
            const key = document.getElementById('nempt-api-key-input').value.trim();
            const lang = document.getElementById('nempt-lang-select').value;

            if (!key) {
                document.getElementById('nempt-api-key-input').style.borderColor = '#f44336';
                return;
            }

            GM_setValue('deepseek_api_key', key);
            GM_setValue('target_lang', lang);
            GM_setValue('is_enabled', true);

            overlay.remove();
            document.getElementById('nempt-notification').remove();
            document.body.style.paddingTop = '0';

            showToast('配置成功！请打开视频并开启字幕');
            GM_log('[YouTube翻译器] 配置已保存');
        });

        document.getElementById('nempt-skip-btn').addEventListener('click', () => {
            overlay.remove();
        });
    }

    // 设置面板
    function showSettings() {
        const existing = document.getElementById('nempt-settings');
        if (existing) existing.remove();

        const panel = document.createElement('div');
        panel.id = 'nempt-settings';
        panel.style.cssText = `
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            width: 400px !important;
            max-width: 90% !important;
            background: #1a1a2e !important;
            border-radius: 16px !important;
            z-index: 100001 !important;
            box-shadow: 0 30px 80px rgba(0,0,0,0.6) !important;
            font-family: 'Microsoft YaHei', sans-serif !important;
        `;

        panel.innerHTML = `
            <div style="padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center;">
                <h3 style="color: #fff; margin: 0; font-size: 18px;">设置</h3>
                <button id="nempt-close-settings" style="
                    background: none;
                    border: none;
                    color: #888;
                    font-size: 24px;
                    cursor: pointer;
                ">&times;</button>
            </div>
            <div style="padding: 20px;">
                <div style="margin-bottom: 16px;">
                    <label style="color: #ccc; display: block; margin-bottom: 8px;">API Key</label>
                    <input type="password" id="nempt-setting-apikey" value="${getApiKey()}"
                        style="width: 100%; padding: 12px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="color: #ccc; display: block; margin-bottom: 8px;">目标语言</label>
                    <select id="nempt-setting-lang" style="width: 100%; padding: 12px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff;">
                        <option value="zh">中文</option>
                        <option value="ja">日语</option>
                        <option value="ko">韩语</option>
                    </select>
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="color: #ccc; display: block; margin-bottom: 8px;">字幕位置</label>
                    <select id="nempt-setting-position" style="width: 100%; padding: 12px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff;">
                        <option value="bottom">底部</option>
                        <option value="top">顶部</option>
                        <option value="center">居中</option>
                        <option value="custom">自定义（可拖动）</option>
                    </select>
                </div>
                <div style="margin-bottom: 16px;">
                    <button id="nempt-reset-position" style="width: 100%; padding: 10px; background: rgba(255,152,0,0.2); border: 1px solid rgba(255,152,0,0.5); border-radius: 8px; color: #FF9800; cursor: pointer; font-size: 13px;">重置字幕位置</button>
                </div>
                <label style="color: #ccc; display: flex; align-items: center; gap: 10px; cursor: pointer;">
                    <input type="checkbox" id="nempt-setting-enabled" ${isEnabled() ? 'checked' : ''}>
                    <span>启用翻译</span>
                </label>
            </div>
            <div style="padding: 20px; display: flex; gap: 10px;">
                <button id="nempt-setting-cancel" style="flex: 1; padding: 12px; background: rgba(255,255,255,0.1); border: none; border-radius: 8px; color: #ccc; cursor: pointer;">取消</button>
                <button id="nempt-setting-save" style="flex: 1; padding: 12px; background: linear-gradient(135deg, #4a9eff, #0066ff); border: none; border-radius: 8px; color: #fff; font-weight: 600; cursor: pointer;">保存</button>
            </div>
        `;

        document.body.appendChild(panel);

        document.getElementById('nempt-close-settings').addEventListener('click', () => panel.remove());
        document.getElementById('nempt-setting-cancel').addEventListener('click', () => panel.remove());

        // 重置位置按钮
        document.getElementById('nempt-reset-position').addEventListener('click', () => {
            GM_setValue('subtitle_position', 'bottom');
            GM_setValue('subtitle_offset', null);
            applySubtitlePosition('bottom');
            document.getElementById('nempt-setting-position').value = 'bottom';
            showToast('位置已重置');
        });

        document.getElementById('nempt-setting-save').addEventListener('click', () => {
            const position = document.getElementById('nempt-setting-position').value;
            GM_setValue('deepseek_api_key', document.getElementById('nempt-setting-apikey').value.trim());
            GM_setValue('target_lang', document.getElementById('nempt-setting-lang').value);
            GM_setValue('subtitle_position', position);
            GM_setValue('is_enabled', document.getElementById('nempt-setting-enabled').checked);

            // 如果不是自定义位置，应用新位置
            if (position !== 'custom') {
                applySubtitlePosition(position);
            }

            panel.remove();
            showToast('设置已保存');
            GM_log('[YouTube翻译器] 设置已保存');
        });
    }

    // 应用字幕位置
    function applySubtitlePosition(position) {
        const container = document.getElementById('nempt-subtitle');
        if (!container) return;

        const s = container.style;
        s.setProperty('position', 'absolute', 'important');
        s.setProperty('z-index', '2147483647', 'important');
        s.setProperty('display', 'block', 'important');

        if (position === 'top') {
            s.setProperty('left', '50%', 'important');
            s.setProperty('top', '80px', 'important');
            s.setProperty('bottom', 'auto', 'important');
            s.setProperty('transform', 'translateX(-50%)', 'important');
        } else if (position === 'center') {
            s.setProperty('left', '50%', 'important');
            s.setProperty('top', '50%', 'important');
            s.setProperty('bottom', 'auto', 'important');
            s.setProperty('transform', 'translate(-50%, -50%)', 'important');
        } else {
            // 默认底部
            s.setProperty('left', '50%', 'important');
            s.setProperty('bottom', '50px', 'important');
            s.setProperty('top', 'auto', 'important');
            s.setProperty('transform', 'translateX(-50%)', 'important');
        }
        
        // 清除自定义偏移
        GM_setValue('subtitle_offset', null);
    }

    // Toast提示
    function showToast(message) {
        const existing = document.querySelector('.nempt-toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'nempt-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed !important;
            bottom: 100px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            background: rgba(76, 175, 80, 0.95) !important;
            color: #fff !important;
            padding: 14px 28px !important;
            border-radius: 30px !important;
            font-size: 14px !important;
            z-index: 100002 !important;
            font-family: 'Microsoft YaHei', sans-serif !important;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // 字幕容器 - 注入到视频播放器内部
    function createSubtitleContainer() {
        const existing = document.getElementById('nempt-subtitle');
        if (existing) return;

        // 找到视频播放器
        const player = document.querySelector('#movie_player') || document.querySelector('.html5-video-player');
        if (!player) {
            GM_log('[YouTube翻译器] 未找到视频播放器');
            return;
        }

        const container = document.createElement('div');
        container.id = 'nempt-subtitle';

        // 相对于视频播放器定位，这样会自动跟随视频
        container.style.cssText = `
            position: absolute !important;
            left: 50% !important;
            bottom: 50px !important;
            transform: translateX(-50%) !important;
            z-index: 2147483647 !important;
            display: none !important;
            pointer-events: none !important;
        `;

        // 字幕内容
        container.innerHTML = `
            <div id="nempt-subtitle-inner" style="
                font-family: 'Microsoft YaHei', sans-serif;
                color: #fff;
                background: rgba(0,0,0,0.9);
                padding: 12px 20px;
                border-radius: 8px;
                text-align: center;
                line-height: 1.5;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                pointer-events: auto;
                cursor: grab;
                user-select: none;
                max-width: 90%;
                word-wrap: break-word;
            "></div>
        `;
        
        // 注入到视频播放器内部
        player.appendChild(container);
        GM_log('[YouTube翻译器] 字幕容器已添加到播放器');

        // 拖动逻辑
        initSubtitleDrag(container);
    }

    // 字幕拖动功能 - 使用相对定位偏移量
    function initSubtitleDrag(container) {
        const inner = container.querySelector('#nempt-subtitle-inner');
        let isDragging = false;
        let startX, startY;
        let offsetBottom = 50;
        let offsetLeft = 0;

        // 从存储读取偏移量
        const savedOffset = GM_getValue('subtitle_offset', null);
        if (savedOffset) {
            offsetBottom = savedOffset.bottom;
            offsetLeft = savedOffset.left || 0;
            updatePosition();
        }

        function updatePosition() {
            const s = container.style;
            if (offsetLeft === 0) {
                s.setProperty('left', '50%', 'important');
                s.setProperty('transform', 'translateX(-50%)', 'important');
            } else {
                s.setProperty('left', `calc(50% + ${offsetLeft}px)`, 'important');
                s.setProperty('transform', 'none', 'important');
            }
            s.setProperty('bottom', offsetBottom + 'px', 'important');
        }

        function startDrag(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            e.preventDefault();
            e.stopPropagation();
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            container.style.setProperty('pointer-events', 'auto', 'important');
            inner.style.cursor = 'grabbing';
            inner.style.background = 'rgba(30,30,30,0.95)';
        }

        function doDrag(e) {
            if (!isDragging) return;
            e.preventDefault();
            e.stopPropagation();

            const dx = e.clientX - startX;
            const dy = startY - e.clientY;

            offsetLeft += dx;
            offsetBottom += dy;
            startX = e.clientX;
            startY = e.clientY;

            updatePosition();
        }

        function endDrag(e) {
            if (!isDragging) return;
            isDragging = false;
            container.style.setProperty('pointer-events', 'none', 'important');
            inner.style.cursor = 'grab';
            inner.style.background = 'rgba(0,0,0,0.9)';

            // 保存偏移量
            GM_setValue('subtitle_offset', { bottom: offsetBottom, left: offsetLeft });
            GM_setValue('subtitle_position', 'custom');
        }

        // 事件委托：绑定在 inner 上，inner.innerHTML 变化不影响
        inner.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', doDrag);
        document.addEventListener('mouseup', endDrag);

        // 触摸支持
        inner.addEventListener('touchstart', (e) => {
            const t = e.touches[0];
            startDrag({ clientX: t.clientX, clientY: t.clientY, target: e.target, preventDefault: () => e.preventDefault(), stopPropagation: () => e.stopPropagation() });
        }, { passive: false });
        document.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            e.preventDefault();
            e.stopPropagation();
            const t = e.touches[0];
            doDrag({ clientX: t.clientX, clientY: t.clientY, preventDefault: () => {} });
        }, { passive: false });
        document.addEventListener('touchend', endDrag);
    }

    // 翻译功能
    const cache = new Map();
    let lastTranslateTime = 0;
    let currentSubtitle = '';

    function processSubtitles() {
        const cues = document.querySelectorAll('.ytp-caption-segment');
        if (!cues.length) return;

        const text = Array.from(cues).map(c => c.textContent).join(' ');
        if (text === currentSubtitle) return;

        currentSubtitle = text;
        translate(text);
    }

    async function translate(text) {
        if (!getApiKey() || !isEnabled()) return;

        if (cache.has(text)) {
            showSubtitle(cache.get(text), text);
            return;
        }

        const now = Date.now();
        if (now - lastTranslateTime < 400) {
            await new Promise(r => setTimeout(r, 400 - (now - lastTranslateTime)));
        }
        lastTranslateTime = Date.now();

        try {
            const translated = await callAPI(text);
            cache.set(text, translated);
            showSubtitle(translated, text);
        } catch (e) {
            GM_log('[YouTube翻译器] 翻译失败: ' + e);
        }
    }

    function callAPI(text) {
        return new Promise((resolve, reject) => {
            const langMap = { zh: '中文', ja: '日语', ko: '韩语' };
            const targetLang = GM_getValue('target_lang', 'zh');

            GM_xmlhttpRequest({
                method: 'POST',
                url: 'https://api.deepseek.com/chat/completions',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getApiKey()}`
                },
                data: JSON.stringify({
                    model: 'deepseek-chat',
                    messages: [{
                        role: 'user',
                        content: `翻译成${langMap[targetLang]}，只返回翻译：\n\n${text}`
                    }],
                    temperature: 0.3,
                    max_tokens: 500
                }),
                timeout: 15000,
                onload: (res) => {
                    try {
                        const data = JSON.parse(res.responseText);
                        if (data.choices && data.choices[0]) {
                            resolve(data.choices[0].message.content.trim().replace(/^["']|["']$/g, ''));
                        } else {
                            reject(new Error('API错误'));
                        }
                    } catch (e) {
                        reject(e);
                    }
                },
                onerror: reject,
                ontimeout: () => reject(new Error('超时'))
            });
        });
    }

    function showSubtitle(translated, original) {
        const container = document.getElementById('nempt-subtitle');
        const inner = document.getElementById('nempt-subtitle-inner');
        if (!container || !inner) return;

        // 上面英文原文，下面中文翻译
        inner.innerHTML = `
            <div style="color: #aaa; font-size: 18px; margin-bottom: 6px;">${original}</div>
            <div style="color: #fff; font-size: 22px;">${translated}</div>
        `;
        container.style.setProperty('display', 'block', 'important');

        clearTimeout(window.hideTimer);
        window.hideTimer = setTimeout(() => {
            container.style.setProperty('display', 'none', 'important');
        }, 4000);
    }

    // 主初始化
    function init() {
        GM_log('[YouTube翻译器] 开始初始化...');

        // 创建UI
        createFloatingButton();
        createNotificationBar();

        // 等待视频播放器加载后再创建字幕容器
        function tryCreateSubtitle() {
            const player = document.querySelector('#movie_player') || document.querySelector('.html5-video-player');
            if (player) {
                createSubtitleContainer();
            }
        }

        // 如果播放器已存在，直接创建
        tryCreateSubtitle();

        // 观察视频播放器加载
        const observer = new MutationObserver(() => {
            tryCreateSubtitle();
        });
        observer.observe(document.body, { childList: true, subtree: true });

        // 添加动画样式
        GM_addStyle(`
            @keyframes nempt-pulse {
                0%, 100% { box-shadow: 0 6px 30px rgba(255, 165, 0, 0.5) !important; }
                50% { box-shadow: 0 8px 40px rgba(255, 165, 0, 0.8) !important; }
            }
        `);

        // 监听视频字幕（防止重复添加）
        function watchVideo() {
            const video = document.querySelector('video');
            if (!video) return;

            // 防止重复添加监听器
            if (video.dataset.nemptRegistered) return;
            video.dataset.nemptRegistered = 'true';

            if (getApiKey() && isEnabled()) {
                video.addEventListener('timeupdate', processSubtitles);
                GM_log('[YouTube翻译器] 开始监听字幕');
            }
        }

        watchVideo();

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                const currentState = GM_getValue('is_enabled', true);
                const newState = !currentState;
                GM_setValue('is_enabled', newState);
                showToast(newState ? '翻译已启用' : '翻译已禁用');

                // 根据新状态更新字幕显示
                if (!newState) {
                    // 禁用时隐藏字幕
                    const container = document.getElementById('nempt-subtitle');
                    if (container) container.style.setProperty('display', 'none', 'important');
                    clearTimeout(window.hideTimer);
                }
            }
        });

        GM_log('[YouTube翻译器] 初始化完成');
    }

    // 延迟执行确保页面加载
    if (document.readyState === 'complete') {
        setTimeout(init, 500);
    } else {
        window.addEventListener('load', () => setTimeout(init, 500));
    }

})();
