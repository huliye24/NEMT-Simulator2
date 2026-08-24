/**
 * NEMT Simulator - Preload Script
 * 
 * Secure bridge between renderer and main process.
 * Exposes limited, safe APIs to the renderer process.
 */

import { contextBridge, ipcRenderer, IpcRendererEvent } from 'electron';
import { IPC_CHANNELS } from '../shared/types';

// Type definitions for exposed API
export interface ElectronAPI {
  // Gateway API
  gateway: {
    health: () => Promise<any>;
    listStrategies: (params?: any) => Promise<any>;
    getStrategy: (id: string) => Promise<any>;
    createStrategy: (data: any) => Promise<any>;
    updateStrategy: (id: string, data: any) => Promise<any>;
    deleteStrategy: (id: string) => Promise<any>;
    listCapsules: (params?: any) => Promise<any>;
    registerCapsule: (data: any) => Promise<any>;
    startBacktest: (data: any) => Promise<any>;
    getBacktest: (id: string) => Promise<any>;
    getMarketData: (symbol: string, interval: string, limit: number) => Promise<any>;
  };

  // Window controls
  window: {
    minimize: () => void;
    maximize: () => void;
    close: () => void;
    isMaximized: () => Promise<boolean>;
  };

  // App info
  app: {
    getVersion: () => Promise<string>;
    getPlatform: () => string;
  };

  // Menu events
  menu: {
    onNewSimulation: (callback: () => void) => () => void;
    onSave: (callback: () => void) => () => void;
    onRunSimulation: (callback: () => void) => () => void;
    onStopSimulation: (callback: () => void) => () => void;
    onSettings: (callback: () => void) => () => void;
    onExport: (callback: (path: string) => void) => () => void;
    onTheoryDocs: (callback: () => void) => () => void;
    onApiDocs: (callback: () => void) => () => void;
  };

  // System
  system: {
    openExternal: (url: string) => void;
  };
}

/**
 * Create a one-time event listener that returns a cleanup function
 */
function createEventListener(channel: string, callback: (...args: any[]) => void): () => void {
  const handler = (_event: IpcRendererEvent, ...args: any[]) => callback(...args);
  ipcRenderer.on(channel, handler);
  return () => ipcRenderer.removeListener(channel, handler);
}

/**
 * Expose protected APIs to renderer
 */
contextBridge.exposeInMainWorld('electron', {
  // Gateway API
  gateway: {
    health: () => ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_HEALTH),
    
    listStrategies: (params?: any) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_LIST_STRATEGIES, params),
    
    getStrategy: (id: string) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_GET_STRATEGY, id),
    
    createStrategy: (data: any) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_CREATE_STRATEGY, data),
    
    updateStrategy: (id: string, data: any) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_UPDATE_STRATEGY, id, data),
    
    deleteStrategy: (id: string) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_DELETE_STRATEGY, id),
    
    listCapsules: (params?: any) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_LIST_CAPSULE, params),
    
    registerCapsule: (data: any) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_REGISTER_CAPSULE, data),
    
    startBacktest: (data: any) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_START_BACKTEST, data),
    
    getBacktest: (id: string) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_GET_BACKTEST, id),
    
    getMarketData: (symbol: string, interval: string, limit: number) => 
      ipcRenderer.invoke(IPC_CHANNELS.GATEWAY_GET_MARKET_DATA, { symbol, interval, limit }),
  },

  // Window controls
  window: {
    minimize: () => ipcRenderer.send(IPC_CHANNELS.WINDOW_MINIMIZE),
    maximize: () => ipcRenderer.send(IPC_CHANNELS.WINDOW_MAXIMIZE),
    close: () => ipcRenderer.send(IPC_CHANNELS.WINDOW_CLOSE),
    isMaximized: () => ipcRenderer.invoke(IPC_CHANNELS.WINDOW_IS_MAXIMIZED),
  },

  // App info
  app: {
    getVersion: () => ipcRenderer.invoke(IPC_CHANNELS.APP_GET_VERSION),
    getPlatform: () => process.platform,
  },

  // Menu events
  menu: {
    onNewSimulation: (callback: () => void) =>
      createEventListener(IPC_CHANNELS.MENU_NEW_SIMULATION, callback),

    onSave: (callback: () => void) =>
      createEventListener(IPC_CHANNELS.MENU_SAVE, callback),

    onRunSimulation: (callback: () => void) =>
      createEventListener(IPC_CHANNELS.MENU_RUN_SIMULATION, callback),

    onStopSimulation: (callback: () => void) =>
      createEventListener(IPC_CHANNELS.MENU_STOP_SIMULATION, callback),

    onSettings: (callback: () => void) =>
      createEventListener(IPC_CHANNELS.MENU_SETTINGS, callback),

    onExport: (callback: (path: string) => void) =>
      createEventListener('file:export', callback),

    onTheoryDocs: (callback: () => void) =>
      createEventListener(IPC_CHANNELS.MENU_THEORY_DOCS, callback),

    onApiDocs: (callback: () => void) =>
      createEventListener(IPC_CHANNELS.MENU_API_DOCS, callback),
  },

  // System
  system: {
    openExternal: (url: string) => ipcRenderer.invoke('system:openExternal', url),
  },
} as ElectronAPI);

// Log preload script loaded
console.log('NEMT Simulator preload script loaded');
