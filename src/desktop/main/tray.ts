/**
 * Tray Manager - System Tray Module
 *
 * Responsibilities:
 * - System tray icon management
 * - Tray context menu
 * - Tray event handling
 */

import { Tray, Menu, nativeImage, BrowserWindow, app } from 'electron';
import * as path from 'path';
import log from 'electron-log';

class TrayManager {
  private tray: Tray | null = null;
  private mainWindow: BrowserWindow | null = null;
  private isQuitting = false;

  setMainWindow(window: BrowserWindow): void {
    this.mainWindow = window;
  }

  setQuitting(value: boolean): void {
    this.isQuitting = value;
  }

  isQuittingApp(): boolean {
    return this.isQuitting;
  }

  create(): Tray {
    const icon = this.createTrayIcon();
    this.tray = new Tray(icon);
    this.tray.setToolTip('NEMT Simulator');

    this.buildContextMenu();

    this.tray.on('click', () => {
      if (this.mainWindow) {
        if (this.mainWindow.isVisible()) {
          this.mainWindow.hide();
        } else {
          this.mainWindow.show();
          this.mainWindow.focus();
        }
      }
    });

    this.tray.on('double-click', () => {
      if (this.mainWindow) {
        this.mainWindow.show();
        this.mainWindow.focus();
      }
    });

    log.info('System tray created');
    return this.tray;
  }

  private createTrayIcon(): Electron.NativeImage {
    const isDev = process.env.NODE_ENV === 'development';
    let iconPath: string;

    if (isDev || !app.isPackaged) {
      iconPath = path.join(__dirname, '..', '..', '..', '..', 'build', 'icon.png');
    } else {
      iconPath = path.join(process.resourcesPath || '', 'build', 'icon.png');
    }

    try {
      const fs = require('fs');
      if (fs.existsSync(iconPath)) {
        return nativeImage.createFromPath(iconPath);
      }
    } catch {
      // Fall through to default
    }

    // Create a simple colored icon as fallback
    return nativeImage.createEmpty();
  }

  private buildContextMenu(): void {
    if (!this.tray) return;

    const contextMenu = Menu.buildFromTemplate([
      {
        label: '显示窗口',
        click: () => {
          this.mainWindow?.show();
          this.mainWindow?.focus();
        },
      },
      {
        label: '隐藏窗口',
        click: () => {
          this.mainWindow?.hide();
        },
      },
      { type: 'separator' },
      {
        label: '运行模拟',
        click: () => {
          this.mainWindow?.show();
          this.mainWindow?.webContents.send('menu:runSimulation');
        },
      },
      {
        label: '停止模拟',
        click: () => {
          this.mainWindow?.webContents.send('menu:stopSimulation');
        },
      },
      { type: 'separator' },
      {
        label: '退出',
        click: () => {
          this.isQuitting = true;
          app.quit();
        },
      },
    ]);

    this.tray.setContextMenu(contextMenu);
  }

  destroy(): void {
    if (this.tray) {
      this.tray.destroy();
      this.tray = null;
    }
  }

  getTray(): Tray | null {
    return this.tray;
  }
}

export default TrayManager;
