"use strict";
/**
 * Window Manager - Electron Window Management Module
 *
 * Responsibilities:
 * - Create and manage main window
 * - Window state persistence
 * - Window events handling
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
exports.WindowManager = void 0;
const electron_1 = require("electron");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const electron_log_1 = __importDefault(require("electron-log"));
const DEFAULT_CONFIG = {
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    title: 'NEMT Simulator',
};
const STATE_FILE = 'window-state.json';
class WindowManager {
    mainWindow = null;
    config;
    isDev;
    statePath;
    constructor(config = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };
        this.isDev = process.env.NODE_ENV === 'development' || process.argv.includes('--dev');
        this.statePath = path.join(process.env.APPDATA || '', 'NEMT Simulator', STATE_FILE);
    }
    getProjectRoot() {
        // __dirname is dist-electron/main, so go up to electron/, then up to project root
        const electronDir = path.join(__dirname, '..', '..');
        if (this.isDev) {
            return path.join(electronDir, '..');
        }
        return path.join(process.resourcesPath, '..', '..');
    }
    getWebDistPath() {
        return path.join(this.getProjectRoot(), 'web', 'dist');
    }
    loadState() {
        try {
            if (fs.existsSync(this.statePath)) {
                const data = fs.readFileSync(this.statePath, 'utf-8');
                return JSON.parse(data);
            }
        }
        catch (error) {
            electron_log_1.default.warn('Failed to load window state:', error);
        }
        // Return default state
        const primaryDisplay = electron_1.screen.getPrimaryDisplay();
        const { width, height } = primaryDisplay.workAreaSize;
        return {
            width: this.config.width,
            height: this.config.height,
            x: Math.floor((width - this.config.width) / 2),
            y: Math.floor((height - this.config.height) / 2),
            isMaximized: false,
        };
    }
    saveState() {
        if (!this.mainWindow)
            return;
        try {
            const bounds = this.mainWindow.getBounds();
            const state = {
                ...bounds,
                isMaximized: this.mainWindow.isMaximized(),
            };
            // Ensure directory exists
            const dir = path.dirname(this.statePath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(this.statePath, JSON.stringify(state, null, 2));
        }
        catch (error) {
            electron_log_1.default.warn('Failed to save window state:', error);
        }
    }
    create() {
        electron_log_1.default.info('Creating main window...');
        const state = this.loadState();
        this.mainWindow = new electron_1.BrowserWindow({
            ...state,
            minWidth: this.config.minWidth,
            minHeight: this.config.minHeight,
            title: this.config.title,
            backgroundColor: '#0f172a',
            show: true,
            // 无边框配置
            frame: false,
            titleBarStyle: 'hidden',
            // 窗口控制按钮使用自定义
            webPreferences: {
                preload: path.join(__dirname, '..', 'preload', 'index.js'),
                contextIsolation: true,
                nodeIntegration: false,
                sandbox: false,
            },
        });
        // 通知渲染进程窗口最大化状态变化
        this.mainWindow.on('maximize', () => {
            this.mainWindow?.webContents.send('window:maximize-change', true);
        });
        this.mainWindow.on('unmaximize', () => {
            this.mainWindow?.webContents.send('window:maximize-change', false);
        });
        // Restore maximized state
        if (state.isMaximized) {
            this.mainWindow.maximize();
        }
        // Show window when ready
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow?.show();
            electron_log_1.default.info('Window shown');
        });
        // Save state on changes
        this.mainWindow.on('resize', () => this.saveState());
        this.mainWindow.on('move', () => this.saveState());
        this.mainWindow.on('close', () => this.saveState());
        // Load content
        this.loadContent();
        return this.mainWindow;
    }
    loadContent() {
        if (!this.mainWindow)
            return;
        if (this.isDev) {
            electron_log_1.default.info('Loading development server...');
            this.mainWindow.loadURL('http://localhost:5173');
            this.mainWindow.webContents.openDevTools();
        }
        else {
            electron_log_1.default.info('Loading production build...');
            const indexPath = path.join(this.getWebDistPath(), 'index.html');
            electron_log_1.default.info(`Loading index from: ${indexPath}`);
            if (fs.existsSync(indexPath)) {
                this.mainWindow.loadFile(indexPath);
            }
            else {
                electron_log_1.default.error(`Index file not found: ${indexPath}`);
            }
        }
    }
    getWindow() {
        return this.mainWindow;
    }
    show() {
        this.mainWindow?.show();
    }
    hide() {
        this.mainWindow?.hide();
    }
    close() {
        this.mainWindow?.close();
    }
    isMaximized() {
        return this.mainWindow?.isMaximized() ?? false;
    }
    minimize() {
        this.mainWindow?.minimize();
    }
    maximize() {
        if (this.mainWindow?.isMaximized()) {
            this.mainWindow.unmaximize();
        }
        else {
            this.mainWindow?.maximize();
        }
    }
}
exports.WindowManager = WindowManager;
exports.default = WindowManager;
