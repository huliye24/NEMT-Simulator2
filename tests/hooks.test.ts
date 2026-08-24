/**
 * Web Hooks Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock fetch for all tests
global.fetch = vi.fn();

describe('useLocalMarket Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty state', async () => {
    const { useLocalMarket } = await import('../src/web/hooks/useLocalMarket');

    const { result } = renderHook(() =>
      useLocalMarket({ symbols: ['BTC/USDT'], autoConnect: false })
    );

    expect(result.current.isConnected).toBe(false);
    expect(result.current.ticker.size).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it('should have connect and disconnect functions', async () => {
    const { useLocalMarket } = await import('../src/web/hooks/useLocalMarket');

    const { result } = renderHook(() =>
      useLocalMarket({ symbols: [], autoConnect: false })
    );

    expect(typeof result.current.connect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
    expect(typeof result.current.subscribe).toBe('function');
    expect(typeof result.current.unsubscribe).toBe('function');
  });
});

describe('useElectronBridge Hook', () => {
  it('should check if electron is available', async () => {
    const { isElectron } = await import('../src/web/hooks/useElectronBridge');

    // In test environment, window.electron is not defined
    expect(isElectron()).toBe(false);
  });

  it('should create ElectronBridge instance', async () => {
    const { ElectronBridge } = await import('../src/web/hooks/useElectronBridge');

    const bridge = new ElectronBridge();

    // Should not throw
    expect(bridge.isAvailable()).toBe(false);
    expect(typeof bridge.getHealth).toBe('function');
    expect(typeof bridge.listStrategies).toBe('function');
  });
});
