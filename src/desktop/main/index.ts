/**
 * NEMT Simulator - Main Process Entry Point
 * 
 * Electron main process with modular architecture:
 * - Window Management
 * - Menu System
 * - System Tray
 * - IPC Communication
 * - Subprocess Management (Go Gateway + Python Engine)
 * - Hot Reload Support
 */

import { app, ipcMain, BrowserWindow, shell, Menu, Tray, nativeImage, NativeImage } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import log from 'electron-log';
import Store from 'electron-store';
import { setupHotReload, isDevelopmentMode } from './hotReload';

// Shared types
import { IPC_CHANNELS, SERVICE_PORTS } from '../shared/types';

// Configure logging
log.transports.file.level = 'info';
log.transports.console.level = 'debug';
log.info('='.repeat(50));
log.info('NEMT Simulator starting...');
log.info(`Version: ${app.getVersion()}`);
log.info(`Platform: ${process.platform}`);
log.info(`Electron: ${process.versions.electron}`);
log.info(`Node: ${process.versions.node}`);
log.info('='.repeat(50));

// Global references
let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let gatewayProcess: ChildProcess | null = null;
let pythonProcess: ChildProcess | null = null;
let isQuitting = false;

// Configuration
const store = new Store({
  defaults: {
    windowBounds: { width: 1400, height: 900 },
    windowMaximized: false,
  },
});

const isDev = process.env.NODE_ENV === 'development';
const isPackaged = app.isPackaged;

// Hot reload watcher instance
let hotReloadWatcher: ReturnType<typeof setupHotReload> | null = null;

// ============================================================================
// Application Lifecycle
// ============================================================================

app.whenReady().then(async () => {
  log.info('App ready, initializing...');

  try {
    // Set up hot reload in development mode
    if (isDev) {
      log.info('Development mode detected, setting up hot reload...');
      hotReloadWatcher = setupHotReload();
    }

    // Start subprocesses
    await startSubprocesses();

    // Create main window
    createWindow();

    // Setup menu
    setupMenu();

    // Setup tray
    setupTray();

    // Register IPC handlers
    registerIPCHandlers();

    log.info('Initialization complete');
  } catch (error) {
    log.error('Initialization failed:', error);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  log.info('Application shutting down...');
  
  // Stop hot reload watcher
  if (hotReloadWatcher) {
    hotReloadWatcher.stop();
    hotReloadWatcher = null;
  }
  
  stopSubprocesses();
});

// ============================================================================
// Window Management
// ============================================================================

function createWindow(): void {
  const { width, height } = store.get('windowBounds') as { width: number; height: number };

  mainWindow = new BrowserWindow({
    width,
    height,
    minWidth: 1024,
    minHeight: 768,
    title: 'NEMT Simulator',
    backgroundColor: '#0a0a0f',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  // Load content
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../web/dist/index.html'));
  }

  // Show when ready
  mainWindow.once('ready-to-show', () => {
    if (store.get('windowMaximized')) {
      mainWindow?.maximize();
    }
    mainWindow?.show();
    log.info('Main window shown');
  });

  // Save window state
  mainWindow.on('resize', saveWindowBounds);
  mainWindow.on('maximize', () => store.set('windowMaximized', true));
  mainWindow.on('unmaximize', () => store.set('windowMaximized', false));
  mainWindow.on('close', (event) => {
    if (tray && !isQuitting) {
      event.preventDefault();
      mainWindow?.hide();
      log.info('Window hidden to tray');
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function saveWindowBounds(): void {
  if (mainWindow && !mainWindow.isMaximized()) {
    store.set('windowBounds', mainWindow.getBounds());
  }
}

// ============================================================================
// Menu System
// ============================================================================

function setupMenu(): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Simulation',
          accelerator: 'CmdOrCtrl+N',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_NEW_SIMULATION),
        },
        {
          label: 'Save',
          accelerator: 'CmdOrCtrl+S',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_SAVE),
        },
        { type: 'separator' },
        {
          label: 'Export Results',
          accelerator: 'CmdOrCtrl+E',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_EXPORT),
        },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Simulation',
      submenu: [
        {
          label: 'Run',
          accelerator: 'F5',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_RUN_SIMULATION),
        },
        {
          label: 'Stop',
          accelerator: 'F6',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_STOP_SIMULATION),
        },
        { type: 'separator' },
        {
          label: 'Noise Scan',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_NOISE_SCAN),
        },
        {
          label: 'Nonlinear Analysis',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_NONLINEAR_ANALYSIS),
        },
        {
          label: 'Full Pipeline',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_FULL_PIPELINE),
        },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'close' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Theory Documentation',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_THEORY_DOCS),
        },
        {
          label: 'API Documentation',
          click: () => sendToRenderer(IPC_CHANNELS.MENU_API_DOCS),
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => showAboutDialog(),
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function sendToRenderer(channel: string, ...args: any[]): void {
  mainWindow?.webContents.send(channel, ...args);
}

function showAboutDialog(): void {
  const { dialog } = require('electron');
  dialog.showMessageBox(mainWindow!, {
    type: 'info',
    title: 'About NEMT Simulator',
    message: 'NEMT Simulator',
    detail: `Version: ${app.getVersion()}\nElectron: ${process.versions.electron}\nNode: ${process.versions.node}\nChrome: ${process.versions.chrome}\n\nNon-Equilibrium Market Theory Trading System`,
  });
}

// ============================================================================
// System Tray
// ============================================================================

function setupTray(): void {
  // Create a simple tray icon (16x16 transparent)
  const iconPath = isPackaged
    ? path.join(process.resourcesPath, 'build', 'icon.png')
    : path.join(__dirname, '../../build', 'icon.png');

  // Create a simple icon if file doesn't exist
  let trayIcon: NativeImage;
  try {
    trayIcon = nativeImage.createFromPath(iconPath);
    if (trayIcon.isEmpty()) {
      trayIcon = createDefaultIcon();
    }
  } catch {
    trayIcon = createDefaultIcon();
  }

  tray = new Tray(trayIcon.resize({ width: 16, height: 16 }));
  tray.setToolTip('NEMT Simulator');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Window',
      click: () => {
        mainWindow?.show();
        mainWindow?.focus();
      },
    },
    { type: 'separator' },
    {
      label: 'Run Simulation',
      click: () => sendToRenderer(IPC_CHANNELS.MENU_RUN_SIMULATION),
    },
    {
      label: 'Stop Simulation',
      click: () => sendToRenderer(IPC_CHANNELS.MENU_STOP_SIMULATION),
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        (app as any).isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);

  tray.on('double-click', () => {
    mainWindow?.show();
    mainWindow?.focus();
  });
}

function createDefaultIcon(): NativeImage {
  // Create a simple 16x16 icon
  return nativeImage.createEmpty();
}

// ============================================================================
// Subprocess Management
// ============================================================================

async function startSubprocesses(): Promise<void> {
  log.info('Starting subprocesses...');

  // Start Go Gateway
  await startGateway();

  // Start Python Engine
  await startPythonEngine();

  log.info('All subprocesses started');
}

async function startGateway(): Promise<void> {
  const gatewayPath = isPackaged
    ? path.join(process.resourcesPath, 'gateway', 'gateway')
    : path.join(__dirname, '../../../dist/gateway/gateway');

  log.info(`Starting Go Gateway: ${gatewayPath}`);

  return new Promise((resolve, reject) => {
    try {
      gatewayProcess = spawn(gatewayPath, [], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          HTTP_PORT: String(SERVICE_PORTS.GATEWAY_HTTP),
          GRPC_PORT: String(SERVICE_PORTS.GATEWAY_GRPC),
        },
      });

      gatewayProcess.stdout?.on('data', (data) => {
        log.info(`[Gateway] ${data.toString().trim()}`);
      });

      gatewayProcess.stderr?.on('data', (data) => {
        log.warn(`[Gateway] ${data.toString().trim()}`);
      });

      gatewayProcess.on('error', (error) => {
        log.error('Gateway process error:', error);
      });

      gatewayProcess.on('exit', (code) => {
        log.info(`Gateway process exited with code ${code}`);
      });

      // Wait for gateway to be ready (check health endpoint)
      setTimeout(resolve, 2000);
    } catch (error) {
      log.warn('Failed to start Gateway (running without it):', error);
      resolve();
    }
  });
}

async function startPythonEngine(): Promise<void> {
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';

  log.info('Starting Python Engine...');

  return new Promise((resolve) => {
    try {
      const nemtOsPath = isPackaged
        ? path.join(process.resourcesPath, 'nemt-os')
        : path.join(__dirname, '../../../src/nemt-os');

      pythonProcess = spawn(pythonPath, ['-m', 'nemt.core.main'], {
        cwd: nemtOsPath,
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHON_GRPC_PORT: String(SERVICE_PORTS.PYTHON_GRPC),
        },
      });

      pythonProcess.stdout?.on('data', (data) => {
        log.info(`[Python] ${data.toString().trim()}`);
        // Forward to renderer
        sendToRenderer(IPC_CHANNELS.PYTHON_LOG, data.toString().trim());
      });

      pythonProcess.stderr?.on('data', (data) => {
        log.warn(`[Python] ${data.toString().trim()}`);
        sendToRenderer(IPC_CHANNELS.PYTHON_ERROR, data.toString().trim());
      });

      pythonProcess.on('error', (error) => {
        log.error('Python process error:', error);
      });

      pythonProcess.on('exit', (code) => {
        log.info(`Python process exited with code ${code}`);
      });

      setTimeout(resolve, 1500);
    } catch (error) {
      log.warn('Failed to start Python Engine (running without it):', error);
      resolve();
    }
  });
}

function stopSubprocesses(): void {
  log.info('Stopping subprocesses...');

  if (gatewayProcess) {
    gatewayProcess.kill('SIGTERM');
    gatewayProcess = null;
  }

  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
    pythonProcess = null;
  }

  log.info('All subprocesses stopped');
}

// ============================================================================
// IPC Handlers
// ============================================================================

function registerIPCHandlers(): void {
  // Window controls
  ipcMain.on(IPC_CHANNELS.WINDOW_MINIMIZE, () => mainWindow?.minimize());
  ipcMain.on(IPC_CHANNELS.WINDOW_MAXIMIZE, () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });
  ipcMain.on(IPC_CHANNELS.WINDOW_CLOSE, () => mainWindow?.close());
  ipcMain.handle(IPC_CHANNELS.WINDOW_IS_MAXIMIZED, () => mainWindow?.isMaximized());

  // App info
  ipcMain.handle(IPC_CHANNELS.APP_GET_VERSION, () => app.getVersion());

  // Gateway health check
  ipcMain.handle(IPC_CHANNELS.GATEWAY_HEALTH, async () => {
    try {
      const response = await fetch(`http://localhost:${SERVICE_PORTS.GATEWAY_HTTP}/health`);
      return await response.json();
    } catch {
      return { status: 'unavailable', error: 'Gateway not running' };
    }
  });

  // Gateway API calls
  ipcMain.handle(IPC_CHANNELS.GATEWAY_LIST_STRATEGIES, async (_, params) => {
    try {
      const response = await fetch(`http://localhost:${SERVICE_PORTS.GATEWAY_HTTP}/api/v1/strategies`);
      return await response.json();
    } catch (error) {
      log.error('Failed to list strategies:', error);
      return { strategies: [], total: 0 };
    }
  });

  ipcMain.handle(IPC_CHANNELS.GATEWAY_GET_STRATEGY, async (_, id) => {
    try {
      const response = await fetch(`http://localhost:${SERVICE_PORTS.GATEWAY_HTTP}/api/v1/strategies/${id}`);
      return await response.json();
    } catch (error) {
      log.error(`Failed to get strategy ${id}:`, error);
      return null;
    }
  });

  ipcMain.handle(IPC_CHANNELS.GATEWAY_CREATE_STRATEGY, async (_, data) => {
    try {
      const response = await fetch(`http://localhost:${SERVICE_PORTS.GATEWAY_HTTP}/api/v1/strategies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return await response.json();
    } catch (error) {
      log.error('Failed to create strategy:', error);
      return { success: false, error: String(error) };
    }
  });

  // Market data
  ipcMain.handle(IPC_CHANNELS.GATEWAY_GET_MARKET_DATA, async (_, { symbol, interval, limit }) => {
    try {
      const response = await fetch(
        `http://localhost:${SERVICE_PORTS.GATEWAY_HTTP}/api/v1/market/${symbol}?interval=${interval}&limit=${limit}`
      );
      return await response.json();
    } catch (error) {
      log.error(`Failed to get market data for ${symbol}:`, error);
      return null;
    }
  });

  // External links
  ipcMain.handle('system:openExternal', async (_, url) => {
    await shell.openExternal(url);
  });

  log.info('IPC handlers registered');
}

// ============================================================================
// Error Handling
// ============================================================================

process.on('uncaughtException', (error) => {
  log.error('Uncaught exception:', error);
});

process.on('unhandledRejection', (reason) => {
  log.error('Unhandled rejection:', reason);
});
