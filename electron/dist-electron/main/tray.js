"use strict";
/**
 * Tray Manager - System Tray Module
 *
 * Responsibilities:
 * - System tray icon management
 * - Tray context menu
 * - Tray event handling
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.TrayManager = void 0;
const electron_1 = require("electron");
const path = __importStar(require("path"));
const electron_log_1 = __importDefault(require("electron-log"));
class TrayManager {
    tray = null;
    mainWindow = null;
    config;
    isQuitting = false;
    constructor(config = {}) {
        this.config = {
            tooltip: 'NEMT Simulator',
            ...config,
        };
    }
    setMainWindow(window) {
        this.mainWindow = window;
    }
    setQuitting(value) {
        this.isQuitting = value;
    }
    isQuittingApp() {
        return this.isQuitting;
    }
    create() {
        // Create tray icon
        const iconPath = this.getIconPath();
        let icon;
        try {
            if (iconPath && require('fs').existsSync(iconPath)) {
                icon = electron_1.nativeImage.createFromPath(iconPath);
            }
            else {
                // Create a simple colored icon as fallback
                icon = electron_1.nativeImage.createEmpty();
            }
        }
        catch {
            icon = electron_1.nativeImage.createEmpty();
        }
        this.tray = new electron_1.Tray(icon);
        this.tray.setToolTip(this.config.tooltip || 'NEMT Simulator');
        // Build context menu
        this.buildContextMenu();
        // Handle click events
        this.tray.on('click', () => {
            if (this.mainWindow) {
                if (this.mainWindow.isVisible()) {
                    this.mainWindow.hide();
                }
                else {
                    this.mainWindow.show();
                    this.mainWindow.focus();
                }
            }
        });
        this.tray.on('double-click', () => {
            if (this.mainWindow) {
                this.mainWindow.show();
                this.mainWindow.focus();
            }
        });
        electron_log_1.default.info('System tray created');
        return this.tray;
    }
    getIconPath() {
        const isDev = process.env.NODE_ENV === 'development';
        if (isDev) {
            return path.join(__dirname, '..', '..', 'build', 'icon.png');
        }
        return path.join(process.resourcesPath, 'build', 'icon.png');
    }
    buildContextMenu() {
        if (!this.tray)
            return;
        const contextMenu = electron_1.Menu.buildFromTemplate([
            {
                label: '显示窗口',
                click: () => {
                    this.mainWindow?.show();
                    this.mainWindow?.focus();
                },
            },
            {
                label: '隐藏窗口',
                click: () => {
                    this.mainWindow?.hide();
                },
            },
            { type: 'separator' },
            {
                label: '运行模拟',
                click: () => {
                    this.mainWindow?.show();
                    this.mainWindow?.webContents.send('menu:runSimulation');
                },
            },
            {
                label: '停止模拟',
                click: () => {
                    this.mainWindow?.webContents.send('menu:stopSimulation');
                },
            },
            { type: 'separator' },
            {
                label: '退出',
                click: () => {
                    this.isQuitting = true;
                    electron_1.app.quit();
                },
            },
        ]);
        this.tray.setContextMenu(contextMenu);
    }
    destroy() {
        if (this.tray) {
            this.tray.destroy();
            this.tray = null;
        }
    }
    getTray() {
        return this.tray;
    }
}
exports.TrayManager = TrayManager;
exports.default = TrayManager;
