/**
 * Window Manager - Electron Window Management Module
 *
 * Responsibilities:
 * - Create and manage main window
 * - Window state persistence
 * - Window events handling
 */

import { BrowserWindow, screen, app } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import log from 'electron-log';

export interface WindowConfig {
  width: number;
  height: number;
  minWidth: number;
  minHeight: number;
  title: string;
}

export interface WindowState {
  width: number;
  height: number;
  x?: number;
  y?: number;
  isMaximized: boolean;
}

const DEFAULT_CONFIG: WindowConfig = {
  width: 1600,
  height: 1000,
  minWidth: 1200,
  minHeight: 800,
  title: 'NEMT Simulator',
};

class WindowManager {
  private mainWindow: BrowserWindow | null = null;
  private config: WindowConfig;
  private isDev: boolean;

  constructor(config: Partial<WindowConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.isDev = process.env.NODE_ENV === 'development';
  }

  getProjectRoot(): string {
    if (this.isDev || !app.isPackaged) {
      return path.join(__dirname, '..', '..', '..', '..');
    }
    return path.join(process.resourcesPath || '', '..');
  }

  getWebDistPath(): string {
    return path.join(this.getProjectRoot(), 'src', 'web', 'dist');
  }

  private getStatePath(): string {
    return path.join(
      app.getPath('userData'),
      'window-state.json'
    );
  }

  private loadState(): WindowState {
    try {
      const statePath = this.getStatePath();
      if (fs.existsSync(statePath)) {
        const data = fs.readFileSync(statePath, 'utf-8');
        return JSON.parse(data);
      }
    } catch (error) {
      log.warn('Failed to load window state:', error);
    }

    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;
    return {
      width: this.config.width,
      height: this.config.height,
      x: Math.floor((width - this.config.width) / 2),
      y: Math.floor((height - this.config.height) / 2),
      isMaximized: false,
    };
  }

  private saveState(): void {
    if (!this.mainWindow) return;

    try {
      const bounds = this.mainWindow.getBounds();
      const state: WindowState = {
        ...bounds,
        isMaximized: this.mainWindow.isMaximized(),
      };

      const statePath = this.getStatePath();
      const dir = path.dirname(statePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      fs.writeFileSync(statePath, JSON.stringify(state, null, 2));
    } catch (error) {
      log.warn('Failed to save window state:', error);
    }
  }

  create(): BrowserWindow {
    log.info('Creating main window...');

    const state = this.loadState();

    this.mainWindow = new BrowserWindow({
      ...state,
      minWidth: this.config.minWidth,
      minHeight: this.config.minHeight,
      title: this.config.title,
      backgroundColor: '#0a0a0f',
      show: false,
      webPreferences: {
        preload: path.join(__dirname, '../preload/index.js'),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: false,
      },
    });

    if (state.isMaximized) {
      this.mainWindow.maximize();
    }

    this.mainWindow.on('resize', () => this.saveState());
    this.mainWindow.on('move', () => this.saveState());
    this.mainWindow.on('close', () => this.saveState());

    this.loadContent();

    return this.mainWindow;
  }

  private loadContent(): void {
    if (!this.mainWindow) return;

    if (this.isDev) {
      log.info('Loading development server...');
      this.mainWindow.loadURL('http://localhost:5173');
      this.mainWindow.webContents.openDevTools();
    } else {
      log.info('Loading production build...');
      const indexPath = path.join(this.getWebDistPath(), 'index.html');
      log.info(`Loading index from: ${indexPath}`);

      if (fs.existsSync(indexPath)) {
        this.mainWindow.loadFile(indexPath);
      } else {
        log.error(`Index file not found: ${indexPath}`);
      }
    }
  }

  getWindow(): BrowserWindow | null {
    return this.mainWindow;
  }

  show(): void {
    this.mainWindow?.show();
  }

  hide(): void {
    this.mainWindow?.hide();
  }

  close(): void {
    this.mainWindow?.close();
  }

  isMaximized(): boolean {
    return this.mainWindow?.isMaximized() ?? false;
  }

  minimize(): void {
    this.mainWindow?.minimize();
  }

  maximize(): void {
    if (this.mainWindow?.isMaximized()) {
      this.mainWindow.unmaximize();
    } else {
      this.mainWindow?.maximize();
    }
  }
}

export default WindowManager;
