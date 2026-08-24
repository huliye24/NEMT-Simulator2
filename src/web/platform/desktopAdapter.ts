/**
 * NEMT Simulator - Desktop Platform Adapter
 * 
 * Provides platform-specific adaptations for desktop environment:
 * - Window controls (minimize, maximize, close)
 * - Native dialogs (file open/save, message boxes)
 * - System integration (tray, menu, shortcuts)
 * - Theme detection
 */

import { isElectron, getElectronAPI } from './useElectronBridge';

export interface PlatformCapabilities {
  supportsDesktop: boolean;
  supportsNativeDialogs: boolean;
  supportsTray: boolean;
  supportsGlobalShortcuts: boolean;
  supportsNotifications: boolean;
}

/**
 * Detect platform capabilities at runtime.
 */
export function detectPlatformCapabilities(): PlatformCapabilities {
  return {
    supportsDesktop: isElectron(),
    supportsNativeDialogs: isElectron(),
    supportsTray: isElectron(),
    supportsGlobalShortcuts: isElectron(),
    supportsNotifications: isElectron() || 'Notification' in window,
  };
}

/**
 * Window controls for desktop mode.
 */
export class DesktopWindowControls {
  private api = isElectron() ? getElectronAPI() : null;

  minimize(): void {
    this.api?.window.minimize();
  }

  maximize(): void {
    this.api?.window.maximize();
  }

  close(): void {
    this.api?.window.close();
  }

  async isMaximized(): Promise<boolean> {
    return this.api?.window.isMaximized() ?? false;
  }
}

/**
 * Native file dialogs for desktop mode.
 */
export class DesktopFileDialog {
  /**
   * Open a file dialog and return selected file paths.
   */
  static async openFile(options?: {
    title?: string;
    filters?: Array<{ name: string; extensions: string[] }>;
    multiSelections?: boolean;
  }): Promise<string[] | null> {
    if (!isElectron()) {
      // Fallback to web file input
      return this.openFileWeb(options);
    }

    // Desktop implementation would use dialog.showOpenDialog
    // For now, return null as placeholder
    console.warn('Desktop file dialog not implemented');
    return null;
  }

  /**
   * Save a file dialog.
   */
  static async saveFile(options?: {
    title?: string;
    defaultPath?: string;
    filters?: Array<{ name: string; extensions: string[] }>;
  }): Promise<string | null> {
    if (!isElectron()) {
      // Web cannot trigger save dialog without download
      console.warn('Save dialog not supported in web mode');
      return null;
    }

    console.warn('Desktop save dialog not implemented');
    return null;
  }

  /**
   * Web fallback for file open.
   */
  private static openFileWeb(
    options?: {
      title?: string;
      filters?: Array<{ name: string; extensions: string[] }>;
      multiSelections?: boolean;
    }
  ): Promise<string[] | null> {
    return new Promise((resolve) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = options?.multiSelections ?? false;

      if (options?.filters) {
        input.accept = options.filters.map(f => f.extensions.map(e => `.${e}`)).flat().join(',');
      }

      input.onchange = () => {
        if (input.files) {
          resolve(Array.from(input.files).map(f => f.name));
        } else {
          resolve(null);
        }
      };

      input.oncancel = () => resolve(null);
      input.click();
    });
  }
}

/**
 * Theme detection for desktop mode.
 */
export class DesktopTheme {
  private static mediaQuery: MediaQueryList | null = null;

  /**
   * Get current theme (light/dark).
   */
  static getTheme(): 'light' | 'dark' {
    if (isElectron()) {
      // In Electron, we could use nativeTheme from electron
      // For now, check CSS media query
    }

    if (this.mediaQuery === null) {
      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    }

    return this.mediaQuery.matches ? 'dark' : 'light';
  }

  /**
   * Check if system is in dark mode.
   */
  static isDarkMode(): boolean {
    return this.getTheme() === 'dark';
  }

  /**
   * Listen for theme changes.
   */
  static onThemeChange(callback: (theme: 'light' | 'dark') => void): () => void {
    if (this.mediaQuery === null) {
      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    }

    const handler = (e: MediaQueryListEvent) => {
      callback(e.matches ? 'dark' : 'light');
    };

    this.mediaQuery.addEventListener('change', handler);

    return () => {
      this.mediaQuery?.removeEventListener('change', handler);
    };
  }
}

/**
 * Desktop notifications.
 */
export class DesktopNotifications {
  /**
   * Show a native notification.
   */
  static show(title: string, options?: {
    body?: string;
    icon?: string;
    tag?: string;
    silent?: boolean;
  }): void {
    if (isElectron()) {
      // In Electron, use Notification from electron
      // For now, use web Notification API
    }

    if ('Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification(title, options);
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then((permission) => {
          if (permission === 'granted') {
            new Notification(title, options);
          }
        });
      }
    }
  }

  /**
   * Request notification permission.
   */
  static async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
}

/**
 * Export singleton instances.
 */
export const windowControls = new DesktopWindowControls();
export const theme = DesktopTheme;
export const notifications = DesktopNotifications;
