"use strict";
/**
 * Menu Manager - Application Menu Module
 *
 * Responsibilities:
 * - Build application menu
 * - Menu event handling
 * - Keyboard shortcuts
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MenuManager = void 0;
const electron_1 = require("electron");
const electron_log_1 = __importDefault(require("electron-log"));
class MenuManager {
    mainWindow = null;
    config;
    constructor(config = {}) {
        this.config = config;
    }
    setMainWindow(window) {
        this.mainWindow = window;
    }
    build() {
        const template = this.buildTemplate();
        const menu = electron_1.Menu.buildFromTemplate(template);
        electron_1.Menu.setApplicationMenu(menu);
        electron_log_1.default.info('Application menu built');
    }
    buildTemplate() {
        return [
            this.buildFileMenu(),
            this.buildEditMenu(),
            this.buildViewMenu(),
            this.buildSimulationMenu(),
            this.buildWindowMenu(),
            this.buildHelpMenu(),
        ];
    }
    buildFileMenu() {
        return {
            label: '文件',
            submenu: [
                {
                    label: '新建模拟',
                    accelerator: 'CmdOrCtrl+N',
                    click: () => this.sendToRenderer('menu:newSimulation'),
                },
                {
                    label: '打开...',
                    accelerator: 'CmdOrCtrl+O',
                    click: async () => {
                        if (!this.mainWindow)
                            return;
                        const result = await electron_1.dialog.showOpenDialog(this.mainWindow, {
                            properties: ['openFile'],
                            filters: [
                                { name: 'CSV Files', extensions: ['csv'] },
                                { name: 'JSON Files', extensions: ['json'] },
                                { name: 'All Files', extensions: ['*'] },
                            ],
                        });
                        if (!result.canceled && result.filePaths.length > 0) {
                            this.sendToRenderer('file:opened', result.filePaths[0]);
                        }
                    },
                },
                {
                    label: '保存',
                    accelerator: 'CmdOrCtrl+S',
                    click: () => this.sendToRenderer('menu:save'),
                },
                {
                    label: '导出结果...',
                    accelerator: 'CmdOrCtrl+E',
                    click: async () => {
                        if (!this.mainWindow)
                            return;
                        const result = await electron_1.dialog.showSaveDialog(this.mainWindow, {
                            filters: [
                                { name: 'PNG Image', extensions: ['png'] },
                                { name: 'JSON Data', extensions: ['json'] },
                                { name: 'CSV Data', extensions: ['csv'] },
                            ],
                        });
                        if (!result.canceled && result.filePath) {
                            this.sendToRenderer('file:export', result.filePath);
                        }
                    },
                },
                { type: 'separator' },
                {
                    label: '设置',
                    accelerator: 'CmdOrCtrl+,',
                    click: () => this.sendToRenderer('menu:settings'),
                },
                { type: 'separator' },
                {
                    label: '退出',
                    accelerator: 'CmdOrCtrl+Q',
                    click: () => {
                        const { app } = require('electron');
                        app.quit();
                    },
                },
            ],
        };
    }
    buildEditMenu() {
        return {
            label: '编辑',
            submenu: [
                { label: '撤销', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
                { label: '重做', accelerator: 'CmdOrCtrl+Shift+Z', role: 'redo' },
                { type: 'separator' },
                { label: '剪切', accelerator: 'CmdOrCtrl+X', role: 'cut' },
                { label: '复制', accelerator: 'CmdOrCtrl+C', role: 'copy' },
                { label: '粘贴', accelerator: 'CmdOrCtrl+V', role: 'paste' },
                { label: '全选', accelerator: 'CmdOrCtrl+A', role: 'selectAll' },
            ],
        };
    }
    buildViewMenu() {
        return {
            label: '视图',
            submenu: [
                {
                    label: '重新加载',
                    accelerator: 'CmdOrCtrl+R',
                    role: 'reload',
                },
                {
                    label: '强制重新加载',
                    accelerator: 'CmdOrCtrl+Shift+R',
                    role: 'forceReload',
                },
                {
                    label: '切换开发者工具',
                    accelerator: 'F12',
                    role: 'toggleDevTools',
                },
                { type: 'separator' },
                { label: '实际大小', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
                { label: '放大', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
                { label: '缩小', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
                { type: 'separator' },
                { label: '全屏', accelerator: 'F11', role: 'togglefullscreen' },
            ],
        };
    }
    buildSimulationMenu() {
        return {
            label: '模拟',
            submenu: [
                {
                    label: '运行模拟',
                    accelerator: 'F5',
                    click: () => this.sendToRenderer('menu:runSimulation'),
                },
                {
                    label: '停止模拟',
                    accelerator: 'Shift+F5',
                    click: () => this.sendToRenderer('menu:stopSimulation'),
                },
                { type: 'separator' },
                {
                    label: '噪声扫描实验',
                    click: () => this.sendToRenderer('menu:noiseScan'),
                },
                {
                    label: '非线性扫描实验',
                    click: () => this.sendToRenderer('menu:nonlinearScan'),
                },
                { type: 'separator' },
                {
                    label: '完整 Pipeline',
                    accelerator: 'CmdOrCtrl+Shift+P',
                    click: () => this.sendToRenderer('menu:fullPipeline'),
                },
            ],
        };
    }
    buildWindowMenu() {
        return {
            label: '窗口',
            submenu: [
                { label: '最小化', role: 'minimize' },
                { label: '关闭', role: 'close' },
            ],
        };
    }
    buildHelpMenu() {
        return {
            label: '帮助',
            submenu: [
                {
                    label: 'NEMT 理论文档',
                    click: () => this.sendToRenderer('menu:theoryDocs'),
                },
                {
                    label: 'API 文档',
                    click: () => this.sendToRenderer('menu:apiDocs'),
                },
                { type: 'separator' },
                {
                    label: '关于 NEMT Simulator',
                    click: () => {
                        electron_1.dialog.showMessageBox(this.mainWindow, {
                            type: 'info',
                            title: '关于 NEMT Simulator',
                            message: 'NEMT Simulator',
                            detail: '版本: 1.0.0\n\n非欧几何市场理论量化交易平台',
                        });
                    },
                },
            ],
        };
    }
    sendToRenderer(channel, ...args) {
        if (this.mainWindow) {
            this.mainWindow.webContents.send(channel, ...args);
        }
    }
}
exports.MenuManager = MenuManager;
exports.default = MenuManager;
