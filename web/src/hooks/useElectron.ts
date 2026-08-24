/**
 * NEMT Simulator - Electron React Hook
 *
 * Provides React hooks for Electron-specific functionality
 * Bridges the gap between renderer process and Electron main process
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ============================================================================
// Type Definitions (mirrors preload.ts)
// ============================================================================

export interface PythonStatus {
  running: boolean;
  error?: string;
  code?: number;
  signal?: string;
}

export interface SystemStats {
  memory: number;
  cpu: number;
  platform: string;
}

export interface GatewayStatus {
  connected: boolean;
  url: string;
  lastCheck: number | null;
  error?: string;
}

export interface ElectronAPI {
  python: {
    execute: (command: string, args?: any[]) => Promise<any>;
    onLog: (callback: (message: string) => void) => () => void;
    onError: (callback: (error: string) => void) => () => void;
    onStatus: (callback: (status: PythonStatus) => void) => () => void;
    getStatus: () => Promise<PythonStatus>;
  };
  file: {
    open: () => Promise<{ canceled: boolean; filePaths: string[] }>;
    save: (content: string, defaultPath?: string) => Promise<{ success: boolean; path?: string }>;
    export: (data: any, filename: string) => Promise<boolean>;
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
    onNoiseScan: (callback: () => void) => () => void;
    onNonlinearScan: (callback: () => void) => () => void;
    onFullPipeline: (callback: () => void) => () => void;
    onSettings: (callback: () => void) => () => void;
    onFileOpened: (callback: (path: string) => void) => () => void;
    onExport: (callback: (path: string) => void) => () => void;
    onTheoryDocs: (callback: () => void) => () => void;
    onApiDocs: (callback: () => void) => () => void;
  };
  data: {
    fetchMarketData: (symbol: string, interval: string, limit: number) => Promise<any>;
    getSavedData: () => Promise<any[]>;
  };
  system: {
    getStats: () => Promise<SystemStats>;
    openExternal: (url: string) => void;
  };
}

// Declare global window interface
declare global {
  interface Window {
    electron?: ElectronAPI;
  }
}

// ============================================================================
// Core Hooks
// ============================================================================

/**
 * Check if running in Electron environment
 */
export function isElectron(): boolean {
  return typeof window !== 'undefined' && window.electron !== undefined;
}

/**
 * Get Electron API instance
 */
export function useElectronAPI(): ElectronAPI | null {
  const [api, setApi] = useState<ElectronAPI | null>(null);

  useEffect(() => {
    setApi(window.electron || null);
  }, []);

  return api;
}

/**
 * Main hook for Electron functionality
 */
export function useElectron() {
  const [isReady, setIsReady] = useState(false);
  const [gatewayStatus, setGatewayStatus] = useState<GatewayStatus>({
    connected: false,
    url: '',
    lastCheck: null,
  });

  const api = useElectronAPI();
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize
  useEffect(() => {
    if (api) {
      setIsReady(true);
      console.log('[useElectron] Electron API available');
    }
  }, [api]);

  // Periodic gateway health check
  useEffect(() => {
    const checkGateway = async () => {
      if (!api) return;

      try {
        const health = await api.python.getStatus();
        setGatewayStatus(prev => ({
          ...prev,
          connected: health.running,
          lastCheck: Date.now(),
          error: undefined,
        }));
      } catch (error) {
        setGatewayStatus(prev => ({
          ...prev,
          connected: false,
          lastCheck: Date.now(),
          error: error instanceof Error ? error.message : 'Unknown error',
        }));
      }
    };

    if (isReady) {
      checkGateway();
      checkIntervalRef.current = setInterval(checkGateway, 30000);
    }

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, [isReady, api]);

  return {
    isElectron: isReady && api !== null,
    api,
    gatewayStatus,
  };
}

// ============================================================================
// Window Controls Hook
// ============================================================================

export interface WindowControls {
  minimize: () => void;
  maximize: () => void;
  close: () => void;
  isMaximized: () => Promise<boolean>;
}

export function useWindowControls(): WindowControls | null {
  const api = useElectronAPI();

  if (!api) return null;

  return {
    minimize: () => api.window.minimize(),
    maximize: () => api.window.maximize(),
    close: () => api.window.close(),
    isMaximized: () => api.window.isMaximized(),
  };
}

// ============================================================================
// Python Status Hook
// ============================================================================

export interface PythonStatusHook {
  status: PythonStatus;
  isRunning: boolean;
  error: string | null;
}

export function usePythonStatus(): PythonStatusHook {
  const [status, setStatus] = useState<PythonStatus>({ running: false });
  const api = useElectronAPI();

  useEffect(() => {
    if (!api) return;

    // Subscribe to status updates
    const unsubscribe = api.python.onStatus((newStatus) => {
      setStatus(newStatus);
    });

    // Get initial status
    api.python.getStatus().then(setStatus).catch(console.error);

    return unsubscribe;
  }, [api]);

  return {
    status,
    isRunning: status.running,
    error: status.error || null,
  };
}

// ============================================================================
// Menu Events Hook
// ============================================================================

export interface MenuEvents {
  onNewSimulation: (callback: () => void) => () => void;
  onSave: (callback: () => void) => () => void;
  onRunSimulation: (callback: () => void) => () => void;
  onStopSimulation: (callback: () => void) => () => void;
  onSettings: (callback: () => void) => () => void;
  onFileOpened: (callback: (path: string) => void) => () => void;
}

export function useMenuEvents(): MenuEvents | null {
  const api = useElectronAPI();

  if (!api) return null;

  return {
    onNewSimulation: (cb) => api.menu.onNewSimulation(cb),
    onSave: (cb) => api.menu.onSave(cb),
    onRunSimulation: (cb) => api.menu.onRunSimulation(cb),
    onStopSimulation: (cb) => api.menu.onStopSimulation(cb),
    onSettings: (cb) => api.menu.onSettings(cb),
    onFileOpened: (cb) => api.menu.onFileOpened(cb),
  };
}

// ============================================================================
// File Operations Hook
// ============================================================================

export interface FileOperations {
  openFile: () => Promise<{ canceled: boolean; filePaths: string[] }>;
  saveFile: (content: string, defaultPath?: string) => Promise<{ success: boolean; path?: string }>;
  exportData: (data: any, filename: string) => Promise<boolean>;
}

export function useFileOperations(): FileOperations | null {
  const api = useElectronAPI();

  if (!api) return null;

  return {
    openFile: () => api.file.open(),
    saveFile: (content, defaultPath) => api.file.save(content, defaultPath),
    exportData: (data, filename) => api.file.export(data, filename),
  };
}

// ============================================================================
// Python Execution Hook
// ============================================================================

export interface PythonExecutor {
  execute: (command: string, args?: any[]) => Promise<any>;
  isExecuting: boolean;
  lastResult: any;
  lastError: string | null;
}

export function usePythonExecutor(): PythonExecutor {
  const [isExecuting, setIsExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [lastError, setLastError] = useState<string | null>(null);
  const api = useElectronAPI();

  const execute = useCallback(async (command: string, args?: any[]) => {
    if (!api) {
      setLastError('Electron API not available');
      return null;
    }

    setIsExecuting(true);
    setLastError(null);

    try {
      const result = await api.python.execute(command, args);
      setLastResult(result);
      return result;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      setLastError(errorMsg);
      return null;
    } finally {
      setIsExecuting(false);
    }
  }, [api]);

  return {
    execute,
    isExecuting,
    lastResult,
    lastError,
  };
}

// ============================================================================
// App Info Hook
// ============================================================================

export interface AppInfo {
  version: string | null;
  platform: string;
}

export function useAppInfo(): AppInfo {
  const [version, setVersion] = useState<string | null>(null);
  const api = useElectronAPI();

  useEffect(() => {
    if (!api) return;
    api.app.getVersion().then(setVersion).catch(() => setVersion(null));
  }, [api]);

  return {
    version,
    platform: api?.app.getPlatform() || 'unknown',
  };
}

// ============================================================================
// Export all types and hooks
// ============================================================================

export default useElectron;
