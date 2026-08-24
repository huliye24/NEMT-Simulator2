/**
 * NEMT Simulator - Electron IPC Bridge
 * 
 * Provides type-safe communication between renderer and main process.
 * Used by the React frontend to interact with Electron.
 */

import { IPC_CHANNELS } from '../desktop/shared/types';

export interface ElectronAPI {
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
  window: {
    minimize: () => void;
    maximize: () => void;
    close: () => void;
    isMaximized: () => Promise<boolean>;
  };
  app: {
    getVersion: () => Promise<string>;
    getPlatform: () => string;
  };
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
  system: {
    openExternal: (url: string) => void;
  };
}

declare global {
  interface Window {
    electron?: ElectronAPI;
  }
}

/**
 * Check if running in Electron environment
 */
export function isElectron(): boolean {
  return typeof window !== 'undefined' && !!window.electron;
}

/**
 * Get Electron API (throws if not in Electron)
 */
export function getElectronAPI(): ElectronAPI {
  if (!isElectron()) {
    throw new Error('Not running in Electron environment');
  }
  return window.electron!;
}

/**
 * Use Electron IPC with fallback for browser development
 */
export class ElectronBridge {
  private api: ElectronAPI | null = null;

  constructor() {
    if (isElectron()) {
      this.api = window.electron!;
    }
  }

  isAvailable(): boolean {
    return this.api !== null;
  }

  // Gateway methods
  async getHealth() {
    if (!this.api) return { status: 'browser' };
    return this.api.gateway.health();
  }

  async listStrategies(params?: any) {
    if (!this.api) return { strategies: [], total: 0 };
    return this.api.gateway.listStrategies(params);
  }

  async getStrategy(id: string) {
    if (!this.api) return null;
    return this.api.gateway.getStrategy(id);
  }

  async createStrategy(data: any) {
    if (!this.api) return { success: false, error: 'Not in Electron' };
    return this.api.gateway.createStrategy(data);
  }

  async startBacktest(data: any) {
    if (!this.api) return { success: false, error: 'Not in Electron' };
    return this.api.gateway.startBacktest(data);
  }

  async getMarketData(symbol: string, interval: string = '1h', limit: number = 100) {
    if (!this.api) return null;
    return this.api.gateway.getMarketData(symbol, interval, limit);
  }

  // Window methods
  minimize() {
    this.api?.window.minimize();
  }

  maximize() {
    this.api?.window.maximize();
  }

  close() {
    this.api?.window.close();
  }

  async isMaximized(): Promise<boolean> {
    return this.api?.window.isMaximized() ?? false;
  }

  // App methods
  async getVersion(): Promise<string> {
    return this.api?.app.getVersion() ?? '1.0.0';
  }

  getPlatform(): string {
    return this.api?.app.getPlatform() ?? 'browser';
  }

  // Menu event listeners
  onNewSimulation(callback: () => void): () => void {
    return this.api?.menu.onNewSimulation(callback) ?? (() => {});
  }

  onSave(callback: () => void): () => void {
    return this.api?.menu.onSave(callback) ?? (() => {});
  }

  onRunSimulation(callback: () => void): () => void {
    return this.api?.menu.onRunSimulation(callback) ?? (() => {});
  }

  onStopSimulation(callback: () => void): () => void {
    return this.api?.menu.onStopSimulation(callback) ?? (() => {});
  }

  onSettings(callback: () => void): () => void {
    return this.api?.menu.onSettings(callback) ?? (() => {});
  }

  // System
  openExternal(url: string) {
    this.api?.system.openExternal(url);
  }
}

// Export singleton instance
export const electronBridge = new ElectronBridge();

// Export for direct use
export const useElectronBridge = () => electronBridge;
