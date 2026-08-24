"use strict";
/**
 * NEMT Simulator - Preload Script
 *
 * Secure bridge between renderer and main process.
 * Exposes limited, safe APIs to the renderer process.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
// IPC Channel constants (must match main process)
const IPC_CHANNELS = {
    PYTHON_EXECUTE: 'python:execute',
    PYTHON_RESULT: 'python:result',
    PYTHON_ERROR: 'python:error',
    PYTHON_STATUS: 'python:status',
    PYTHON_LOG: 'python:log',
    FILE_OPEN: 'file:open',
    FILE_SAVE: 'file:save',
    FILE_EXPORT: 'file:export',
    WINDOW_MINIMIZE: 'window:minimize',
    WINDOW_MAXIMIZE: 'window:maximize',
    WINDOW_CLOSE: 'window:close',
    WINDOW_MAXIMIZE_CHANGE: 'window:maximize-change',
    APP_GET_VERSION: 'app:getVersion',
    APP_GET_PLATFORM: 'app:getPlatform',
    DATA_FETCH: 'data:fetch',
    DATA_GET_SAVED: 'data:getSaved',
    SYSTEM_STATS: 'system:stats',
    SYSTEM_OPEN_EXTERNAL: 'system:openExternal',
    // Logging
    LOG_ERROR: 'log:error',
};
/**
 * Create a one-time event listener that returns a cleanup function
 */
function createEventListener(channel, callback) {
    const handler = (_event, ...args) => callback(...args);
    electron_1.ipcRenderer.on(channel, handler);
    return () => electron_1.ipcRenderer.removeListener(channel, handler);
}
/**
 * Expose protected APIs to renderer
 */
electron_1.contextBridge.exposeInMainWorld('electron', {
    // Python/NEMT Core communication
    python: {
        execute: (command, args = []) => electron_1.ipcRenderer.invoke(IPC_CHANNELS.PYTHON_EXECUTE, command, args),
        onLog: (callback) => createEventListener(IPC_CHANNELS.PYTHON_LOG, callback),
        onError: (callback) => createEventListener(IPC_CHANNELS.PYTHON_ERROR, callback),
        onStatus: (callback) => createEventListener(IPC_CHANNELS.PYTHON_STATUS, callback),
        getStatus: () => electron_1.ipcRenderer.invoke('python:getStatus'),
    },
    // File operations
    file: {
        open: () => electron_1.ipcRenderer.invoke(IPC_CHANNELS.FILE_OPEN),
        save: (content, defaultPath) => electron_1.ipcRenderer.invoke(IPC_CHANNELS.FILE_SAVE, content, defaultPath),
        export: async (data, filename) => {
            try {
                const result = await electron_1.ipcRenderer.invoke(IPC_CHANNELS.FILE_SAVE, JSON.stringify(data, null, 2), filename);
                return result.success;
            }
            catch {
                return false;
            }
        },
    },
    // Window operations
    window: {
        minimize: () => electron_1.ipcRenderer.send(IPC_CHANNELS.WINDOW_MINIMIZE),
        maximize: () => electron_1.ipcRenderer.send(IPC_CHANNELS.WINDOW_MAXIMIZE),
        close: () => electron_1.ipcRenderer.send(IPC_CHANNELS.WINDOW_CLOSE),
        isMaximized: () => electron_1.ipcRenderer.invoke('window:isMaximized'),
        onMaximizeChange: (callback) => createEventListener(IPC_CHANNELS.WINDOW_MAXIMIZE_CHANGE, callback),
    },
    // App info
    app: {
        getVersion: () => electron_1.ipcRenderer.invoke(IPC_CHANNELS.APP_GET_VERSION),
        getPlatform: () => process.platform,
    },
    // Menu events - map main process menu events to renderer
    menu: {
        onNewSimulation: (callback) => createEventListener('menu:newSimulation', callback),
        onSave: (callback) => createEventListener('menu:save', callback),
        onRunSimulation: (callback) => createEventListener('menu:runSimulation', callback),
        onStopSimulation: (callback) => createEventListener('menu:stopSimulation', callback),
        onNoiseScan: (callback) => createEventListener('menu:noiseScan', callback),
        onNonlinearScan: (callback) => createEventListener('menu:nonlinearScan', callback),
        onFullPipeline: (callback) => createEventListener('menu:fullPipeline', callback),
        onSettings: (callback) => createEventListener('menu:settings', callback),
        onFileOpened: (callback) => createEventListener('file:opened', callback),
        onExport: (callback) => createEventListener('file:export', callback),
        onTheoryDocs: (callback) => createEventListener('menu:theoryDocs', callback),
        onApiDocs: (callback) => createEventListener('menu:apiDocs', callback),
    },
    // Data operations
    data: {
        fetchMarketData: (symbol, interval, limit) => electron_1.ipcRenderer.invoke(IPC_CHANNELS.DATA_FETCH, { symbol, interval, limit }),
        getSavedData: () => electron_1.ipcRenderer.invoke(IPC_CHANNELS.DATA_GET_SAVED),
    },
    // System
    system: {
        getStats: () => electron_1.ipcRenderer.invoke(IPC_CHANNELS.SYSTEM_STATS),
        openExternal: (url) => electron_1.ipcRenderer.invoke('system:openExternal', url),
    },
    // Logging
    log: {
        error: (level, message, details) => electron_1.ipcRenderer.send(IPC_CHANNELS.LOG_ERROR, { level, message, details }),
    },
});
// Log preload script loaded
console.log('NEMT Simulator preload script loaded');
