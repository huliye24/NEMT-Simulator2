"use strict";
/**
 * Preload API - Bridge API between main and renderer
 *
 * Provides type-safe access to IPC channels from renderer process.
 */
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
// Create event listener with cleanup
function createEventListener(channel, callback) {
    const handler = (_event, ...args) => callback(...args);
    electron_1.ipcRenderer.on(channel, handler);
    return () => electron_1.ipcRenderer.removeListener(channel, handler);
}
// Expose APIs
electron_1.contextBridge.exposeInMainWorld('electron', {
    // Go Gateway
    gateway: {
        health: () => electron_1.ipcRenderer.invoke('gateway:health'),
        listStrategies: (params) => electron_1.ipcRenderer.invoke('gateway:listStrategies', params),
        getStrategy: (id) => electron_1.ipcRenderer.invoke('gateway:getStrategy', id),
        createStrategy: (data) => electron_1.ipcRenderer.invoke('gateway:createStrategy', data),
        updateStrategy: (id, data) => electron_1.ipcRenderer.invoke('gateway:updateStrategy', id, data),
        deleteStrategy: (id) => electron_1.ipcRenderer.invoke('gateway:deleteStrategy', id),
        listCapsules: (params) => electron_1.ipcRenderer.invoke('gateway:listCapsules', params),
        registerCapsule: (data) => electron_1.ipcRenderer.invoke('gateway:registerCapsule', data),
        startBacktest: (data) => electron_1.ipcRenderer.invoke('gateway:startBacktest', data),
        getBacktest: (id) => electron_1.ipcRenderer.invoke('gateway:getBacktest', id),
        getMarketData: (symbol, interval, limit) => electron_1.ipcRenderer.invoke('gateway:getMarketData', { symbol, interval, limit }),
        getLatestPrice: (symbol) => electron_1.ipcRenderer.invoke('gateway:getLatestPrice', symbol),
        getSupportedSymbols: () => electron_1.ipcRenderer.invoke('gateway:getSupportedSymbols'),
    },
    // WebSocket
    ws: {
        connect: () => electron_1.ipcRenderer.invoke('ws:connect'),
        disconnect: () => electron_1.ipcRenderer.send('ws:disconnect'),
        subscribe: (symbols) => electron_1.ipcRenderer.send('ws:subscribe', symbols),
        unsubscribe: (symbols) => electron_1.ipcRenderer.send('ws:unsubscribe', symbols),
        onTicker: (callback) => createEventListener('ws:ticker', callback),
        onKline: (callback) => createEventListener('ws:kline', callback),
        isConnected: () => electron_1.ipcRenderer.sendSync('ws:isConnected'),
    },
    // Python (legacy)
    python: {
        execute: (command, args = []) => electron_1.ipcRenderer.invoke('python:execute', command, args),
        getStatus: () => electron_1.ipcRenderer.invoke('python:getStatus'),
        onLog: (callback) => createEventListener('python:log', callback),
        onError: (callback) => createEventListener('python:error', callback),
        onStatus: (callback) => createEventListener('python:status', callback),
    },
    // File
    file: {
        open: () => electron_1.ipcRenderer.invoke('file:open'),
        save: (content, defaultPath) => electron_1.ipcRenderer.invoke('file:save', content, defaultPath),
        export: (data, filename) => electron_1.ipcRenderer.invoke('file:export', data, filename),
    },
    // Window
    window: {
        minimize: () => electron_1.ipcRenderer.send('window:minimize'),
        maximize: () => electron_1.ipcRenderer.send('window:maximize'),
        close: () => electron_1.ipcRenderer.send('window:close'),
        isMaximized: () => electron_1.ipcRenderer.invoke('window:isMaximized'),
        onMaximizeChange: (callback) => createEventListener('window:maximize-change', callback),
    },
    // App
    app: {
        getVersion: () => electron_1.ipcRenderer.invoke('app:getVersion'),
        getPlatform: () => process.platform,
    },
    // Menu
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
    },
});
console.log('NEMT Simulator preload API loaded');
