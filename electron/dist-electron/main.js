"use strict";
/**
 * NEMT Simulator - Main Entry Point
 *
 * Phase 2 Refactored:
 * - Modular architecture with dedicated modules
 * - Go Gateway integration
 * - WebSocket support
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const electron_log_1 = __importDefault(require("electron-log"));
const window_1 = __importDefault(require("./main/window"));
const menu_1 = __importDefault(require("./main/menu"));
const tray_1 = __importDefault(require("./main/tray"));
const ipc_1 = __importDefault(require("./main/ipc"));
// Configure logging
electron_log_1.default.transports.file.level = 'info';
electron_log_1.default.transports.console.level = 'debug';
electron_log_1.default.info('NEMT Simulator starting...');
// Global references
let windowManager;
let menuManager;
let trayManager;
let ipcClient;
// ============================================================================
// Application Lifecycle
// ============================================================================
electron_1.app.whenReady().then(() => {
    electron_log_1.default.info('App ready, initializing...');
    // Initialize managers
    initManagers();
    // Setup IPC handlers
    setupIPCHandlers();
    // Create window
    const mainWindow = windowManager.create();
    // Setup menu
    menuManager.setMainWindow(mainWindow);
    menuManager.build();
    // Setup tray
    trayManager.setMainWindow(mainWindow);
    trayManager.create();
    // Connect to Go Gateway
    connectToGateway();
    // Handle window close
    mainWindow.on('close', (event) => {
        if (!trayManager.isQuittingApp()) {
            event.preventDefault();
            windowManager.hide();
            electron_log_1.default.info('Window hidden to tray');
        }
    });
    mainWindow.on('closed', () => {
        windowManager = null;
    });
    electron_log_1.default.info('Initialization complete');
});
electron_1.app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
    }
});
electron_1.app.on('activate', () => {
    if (electron_1.BrowserWindow.getAllWindows().length === 0) {
        const mainWindow = windowManager.create();
        windowManager.show();
    }
    else {
        windowManager.show();
    }
});
electron_1.app.on('before-quit', () => {
    trayManager.setQuitting(true);
    ipcClient?.disconnectWebSocket();
});
// ============================================================================
// Initialization
// ============================================================================
function initManagers() {
    windowManager = new window_1.default();
    menuManager = new menu_1.default();
    trayManager = new tray_1.default();
    ipcClient = new ipc_1.default();
}
function setupIPCHandlers() {
    // Gateway handlers
    electron_1.ipcMain.handle('gateway:health', async () => {
        return ipcClient.health();
    });
    electron_1.ipcMain.handle('gateway:listStrategies', async (_, params) => {
        return ipcClient.listStrategies(params);
    });
    electron_1.ipcMain.handle('gateway:getStrategy', async (_, id) => {
        return ipcClient.getStrategy(id);
    });
    electron_1.ipcMain.handle('gateway:createStrategy', async (_, data) => {
        return ipcClient.createStrategy(data);
    });
    electron_1.ipcMain.handle('gateway:updateStrategy', async (_, id, data) => {
        return ipcClient.updateStrategy(id, data);
    });
    electron_1.ipcMain.handle('gateway:deleteStrategy', async (_, id) => {
        return ipcClient.deleteStrategy(id);
    });
    electron_1.ipcMain.handle('gateway:listCapsules', async (_, params) => {
        return ipcClient.listCapsules(params);
    });
    electron_1.ipcMain.handle('gateway:registerCapsule', async (_, data) => {
        return ipcClient.registerCapsule(data);
    });
    electron_1.ipcMain.handle('gateway:startBacktest', async (_, data) => {
        return ipcClient.startBacktest(data);
    });
    electron_1.ipcMain.handle('gateway:getBacktest', async (_, id) => {
        return ipcClient.getBacktest(id);
    });
    electron_1.ipcMain.handle('gateway:getMarketData', async (_, { symbol, interval, limit }) => {
        return ipcClient.getMarketData(symbol, interval, limit);
    });
    electron_1.ipcMain.handle('gateway:getLatestPrice', async (_, symbol) => {
        return ipcClient.getLatestPrice(symbol);
    });
    electron_1.ipcMain.handle('gateway:getSupportedSymbols', async () => {
        return ipcClient.getSupportedSymbols();
    });
    // Window handlers
    electron_1.ipcMain.on('window:minimize', () => {
        windowManager.minimize();
    });
    electron_1.ipcMain.on('window:maximize', () => {
        windowManager.maximize();
    });
    electron_1.ipcMain.on('window:close', () => {
        windowManager.close();
    });
    electron_1.ipcMain.handle('window:isMaximized', () => {
        return windowManager.isMaximized();
    });
    // App handlers
    electron_1.ipcMain.handle('app:getVersion', () => {
        return electron_1.app.getVersion();
    });
    // System handlers
    electron_1.ipcMain.handle('system:openExternal', async (_, url) => {
        await electron_1.shell.openExternal(url);
    });
    // WebSocket handlers
    electron_1.ipcMain.on('ws:connect', async () => {
        try {
            await ipcClient.connectWebSocket();
        }
        catch (error) {
            electron_log_1.default.error('Failed to connect WebSocket:', error);
        }
    });
    electron_1.ipcMain.on('ws:disconnect', () => {
        ipcClient.disconnectWebSocket();
    });
    electron_1.ipcMain.on('ws:subscribe', (_, symbols) => {
        ipcClient.subscribe(symbols, (data) => {
            windowManager.getWindow()?.webContents.send('ws:ticker', data);
        });
    });
    electron_1.ipcMain.on('ws:unsubscribe', (_, symbols) => {
        ipcClient.unsubscribe(symbols);
    });
    // Logging handler - writes frontend errors to log file
    electron_1.ipcMain.on('log:error', (_, payload) => {
        const { level, message, details } = payload;
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [${(level || 'ERROR').toUpperCase()}] [FRONTEND] ${message}`;
        if (details) {
            electron_log_1.default.error(logMessage + '\n' + details);
        }
        else {
            electron_log_1.default.error(logMessage);
        }
    });
    electron_log_1.default.info('IPC handlers registered');
}
// ============================================================================
// Gateway Connection
// ============================================================================
async function connectToGateway() {
    try {
        const health = await ipcClient.health();
        electron_log_1.default.info('Go Gateway connected:', health);
        // Connect WebSocket
        try {
            await ipcClient.connectWebSocket();
            ipcClient.subscribe(['BTCUSDT', 'ETHUSDT'], (data) => {
                windowManager.getWindow()?.webContents.send('market:ticker', data);
            });
            electron_log_1.default.info('WebSocket connected');
        }
        catch (error) {
            electron_log_1.default.warn('WebSocket connection failed (non-critical):', error);
        }
    }
    catch (error) {
        electron_log_1.default.warn('Go Gateway not available (running in standalone mode):', error);
        // Continue in standalone mode without gateway
    }
}
// ============================================================================
// Error Handling
// ============================================================================
process.on('uncaughtException', (error) => {
    electron_log_1.default.error('Uncaught exception:', error);
});
process.on('unhandledRejection', (reason) => {
    electron_log_1.default.error('Unhandled rejection:', reason);
});
