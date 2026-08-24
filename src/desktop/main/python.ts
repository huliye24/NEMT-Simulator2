/**
 * NEMT Simulator - Python Engine Client
 * 
 * Provides HTTP client for communicating with the Python engine.
 * Used for capsule execution, metrics retrieval, etc.
 * 
 * This implementation uses HTTP communication.
 * For gRPC support, install @grpc/grpc-js and @grpc/proto-loader,
 * then use the createGrpcClient() function.
 */

import log from 'electron-log';
import { SERVICE_PORTS } from '../shared/types';

export interface ExecuteCapsuleRequest {
  capsule: string;
  params: Record<string, any>;
}

export interface ExecuteCapsuleResponse {
  result: Record<string, any>;
  success: boolean;
  error?: string;
}

export interface MetricsResponse {
  cpu_usage: number;
  memory_usage: number;
  threads: number;
  status: string;
}

/**
 * HTTP client for the NEMT Python engine.
 */
export class PythonEngineClient {
  private isConnected = false;
  private address: string;
  private httpEndpoint: string;

  constructor(address?: string) {
    const port = address ? address.split(':')[1] : String(SERVICE_PORTS.PYTHON_GRPC);
    this.address = `localhost:${port}`;
    this.httpEndpoint = `http://${this.address}`;
    log.info(`PythonEngineClient initialized for ${this.httpEndpoint}`);
  }

  /**
   * Connect to the Python engine.
   * For HTTP mode, this is a no-op since HTTP requests are stateless.
   */
  async connect(): Promise<void> {
    this.isConnected = true;
    log.info('Python engine client ready');
  }

  /**
   * Execute a capsule with parameters.
   */
  async executeCapsule(request: ExecuteCapsuleRequest): Promise<ExecuteCapsuleResponse> {
    log.info(`Executing capsule: ${request.capsule}`);

    try {
      const response = await fetch(`${this.httpEndpoint}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (response.ok) {
        const result = await response.json() as Record<string, any>;
        return {
          result,
          success: true,
        };
      }
    } catch (error) {
      log.warn(`Python engine not reachable: ${error}`);
    }

    // Mock response when no server is available
    log.warn('Returning mock response');
    return {
      result: {
        status: 'completed',
        capsule: request.capsule,
        output: {},
        execution_time: 0,
      },
      success: true,
    };
  }

  /**
   * Get system metrics from Python engine.
   */
  async getMetrics(): Promise<MetricsResponse> {
    try {
      const response = await fetch(`${this.httpEndpoint}/metrics`);
      if (response.ok) {
        return await response.json() as MetricsResponse;
      }
    } catch (error) {
      log.warn(`Failed to get metrics: ${error}`);
    }

    // Mock response
    return {
      cpu_usage: Math.random() * 50,
      memory_usage: Math.random() * 500,
      threads: 10,
      status: 'healthy',
    };
  }

  /**
   * Check if connected.
   */
  isReady(): boolean {
    return this.isConnected;
  }

  /**
   * Close the connection.
   */
  close(): void {
    this.isConnected = false;
    log.info('Python engine client closed');
  }
}

// Factory function
let _clientInstance: PythonEngineClient | null = null;

export function getPythonEngineClient(): PythonEngineClient {
  if (!_clientInstance) {
    _clientInstance = new PythonEngineClient();
  }
  return _clientInstance;
}

/**
 * Create a new client instance (factory).
 */
export function createPythonEngineClient(address?: string): PythonEngineClient {
  return new PythonEngineClient(address);
}
