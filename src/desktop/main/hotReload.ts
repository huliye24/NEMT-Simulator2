/**
 * NEMT Simulator - Hot Reload Module
 * 
 * Provides hot module replacement (HMR) support for development mode.
 * Automatically detects file changes and triggers reloads.
 */

import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';

export interface HotReloadConfig {
  /** Watch paths */
  watchPaths: string[];
  /** File extensions to watch */
  extensions: string[];
  /** Debounce delay in ms */
  debounceMs: number;
  /** Enable auto-reload */
  autoReload: boolean;
}

const DEFAULT_CONFIG: HotReloadConfig = {
  watchPaths: [
    path.join(__dirname, '../../web/src'),
    path.join(__dirname, '../../web/dist'),
  ],
  extensions: ['.ts', '.tsx', '.js', '.jsx', '.json', '.css'],
  debounceMs: 300,
  autoReload: true,
};

/**
 * File watcher for development mode hot reload.
 */
export class HotReloadWatcher extends EventEmitter {
  private config: HotReloadConfig;
  private watchers: Map<string, fs.FSWatcher> = new Map();
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private isRunning = false;

  constructor(config: Partial<HotReloadConfig> = {}) {
    super();
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Start watching files for changes.
   */
  start(): void {
    if (this.isRunning) return;

    console.log('[HotReload] Starting file watcher...');
    this.isRunning = true;

    for (const watchPath of this.config.watchPaths) {
      this.watchDirectory(watchPath);
    }
  }

  /**
   * Stop watching files.
   */
  stop(): void {
    if (!this.isRunning) return;

    console.log('[HotReload] Stopping file watcher...');
    this.isRunning = false;

    for (const watcher of this.watchers.values()) {
      watcher.close();
    }
    this.watchers.clear();

    for (const timer of this.debounceTimers.values()) {
      clearTimeout(timer);
    }
    this.debounceTimers.clear();
  }

  /**
   * Watch a directory recursively.
   */
  private watchDirectory(dirPath: string): void {
    try {
      if (!fs.existsSync(dirPath)) {
        console.warn(`[HotReload] Path does not exist: ${dirPath}`);
        return;
      }

      const watcher = fs.watch(
        dirPath,
        { recursive: true },
        (eventType, filename) => this.handleEvent(eventType, filename)
      );

      watcher.on('error', (error) => {
        console.error(`[HotReload] Watcher error: ${error}`);
      });

      this.watchers.set(dirPath, watcher);
      console.log(`[HotReload] Watching: ${dirPath}`);
    } catch (error) {
      console.error(`[HotReload] Failed to watch ${dirPath}:`, error);
    }
  }

  /**
   * Handle file change event.
   */
  private handleEvent(eventType: string, filename: string | null): void {
    if (!filename) return;

    const ext = path.extname(filename).toLowerCase();
    if (!this.config.extensions.includes(ext)) return;

    const fullPath = filename;
    this.debouncedEmit(fullPath);
  }

  /**
   * Debounce file change events.
   */
  private debouncedEmit(filePath: string): void {
    const existingTimer = this.debounceTimers.get(filePath);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    const timer = setTimeout(() => {
      this.debounceTimers.delete(filePath);
      this.emit('change', filePath);
      console.log(`[HotReload] File changed: ${filePath}`);
    }, this.config.debounceMs);

    this.debounceTimers.set(filePath, timer);
  }

  /**
   * Check if watching is active.
   */
  getIsRunning(): boolean {
    return this.isRunning;
  }
}

// Development mode utilities
export function isDevelopmentMode(): boolean {
  return process.env.NODE_ENV === 'development' || !process.env.NODE_ENV;
}

export function getDevServerUrl(): string {
  return process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173';
}

/**
 * Initialize hot reload for the main process.
 */
export function setupHotReload(): HotReloadWatcher | null {
  if (!isDevelopmentMode()) {
    console.log('[HotReload] Not in development mode, skipping HMR setup');
    return null;
  }

  const watcher = new HotReloadWatcher();

  watcher.on('change', (filePath: string) => {
    console.log(`[HotReload] Change detected: ${filePath}`);
    // In a full implementation, this would:
    // 1. Notify the renderer process
    // 2. Trigger Vite HMR if applicable
    // 3. Log the change for debugging
  });

  watcher.start();

  // Handle process exit
  process.on('exit', () => watcher.stop());
  process.on('SIGINT', () => {
    watcher.stop();
    process.exit(0);
  });

  return watcher;
}

/**
 * Module-level hot reload hook.
 * 
 * Usage in renderer:
 * ```typescript
 * if (import.meta.hot) {
 *   import.meta.hot.accept(() => {
 *     console.log('Module reloaded');
 *   });
 * }
 * ```
 */
export interface HotModule {
  accept(callback?: () => void): void;
  decline(): void;
  addStatusHandler(callback: (status: string) => void): void;
}

declare global {
  interface ImportMeta {
    hot?: HotModule;
  }
}
