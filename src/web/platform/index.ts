/**
 * NEMT Simulator - Platform Index
 * 
 * Central export for all platform-specific functionality.
 */

export {
  DesktopWindowControls,
  DesktopFileDialog,
  DesktopTheme,
  DesktopNotifications,
  windowControls,
  theme,
  notifications,
  detectPlatformCapabilities,
  type PlatformCapabilities,
} from './desktopAdapter';
