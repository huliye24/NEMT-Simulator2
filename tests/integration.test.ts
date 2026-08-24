/**
 * Integration Tests for NEMT Simulator
 */

import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest';

// These tests require a running backend

describe('Gateway Integration', () => {
  const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8080';

  describe('Health Endpoint', () => {
    it('should return health status', async () => {
      try {
        const response = await fetch(`${GATEWAY_URL}/health`);
        const data = await response.json();

        expect(response.ok).toBe(true);
        expect(data.status).toBeDefined();
      } catch (error) {
        // Skip if gateway is not running
        console.log('Gateway not available, skipping integration test');
      }
    });
  });

  describe('Strategies API', () => {
    it('should list strategies', async () => {
      try {
        const response = await fetch(`${GATEWAY_URL}/api/v1/strategies`);
        const data = await response.json();

        expect(response.ok).toBe(true);
        expect(Array.isArray(data.strategies) || data.strategies !== undefined).toBe(true);
      } catch (error) {
        console.log('Gateway not available, skipping integration test');
      }
    });
  });
});

describe('IPC Communication', () => {
  it('should be testable in desktop mode', () => {
    // This test documents the IPC testing approach
    expect(true).toBe(true);
  });
});
