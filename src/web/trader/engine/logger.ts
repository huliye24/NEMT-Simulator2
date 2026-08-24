/**
 * Copyright 2026 NEMT Lab
 *
 * NEMT Logger
 */

export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warning: 2,
  error: 3,
  critical: 4,
};

class Logger {
  private level: LogLevel = 'info';
  private handlers: Array<(level: LogLevel, message: string, data?: unknown) => void> = [];

  setLevel(level: LogLevel): void {
    this.level = level;
  }

  addHandler(handler: (level: LogLevel, message: string, data?: unknown) => void): () => void {
    this.handlers.push(handler);
    return () => {
      const index = this.handlers.indexOf(handler);
      if (index > -1) {
        this.handlers.splice(index, 1);
      }
    };
  }

  private shouldLog(level: LogLevel): boolean {
    return LEVEL_PRIORITY[level] >= LEVEL_PRIORITY[this.level];
  }

  private log(level: LogLevel, message: string, data?: unknown): void {
    if (!this.shouldLog(level)) return;

    const timestamp = new Date().toISOString();
    const formatted = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

    console.log(formatted, data || '');

    for (const handler of this.handlers) {
      handler(level, formatted, data);
    }
  }

  debug(message: string, data?: unknown): void {
    this.log('debug', message, data);
  }

  info(message: string, data?: unknown): void {
    this.log('info', message, data);
  }

  warning(message: string, data?: unknown): void {
    this.log('warning', message, data);
  }

  error(message: string, data?: unknown): void {
    this.log('error', message, data);
  }

  critical(message: string, data?: unknown): void {
    this.log('critical', message, data);
  }
}

export const logger = new Logger();

export const DEBUG = 'debug';
export const INFO = 'info';
export const WARNING = 'warning';
export const ERROR = 'error';
export const CRITICAL = 'critical';
