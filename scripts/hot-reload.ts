/**
 * NEMT Simulator - Hot Reload Utility
 * 
 * Watches for file changes in dist folder and reloads the Electron app.
 */

import { watch } from 'chokidar';
import { spawn } from 'child_process';
import * as path from 'path';

const DIST_PATH = path.join(__dirname, '..', '..', 'dist');
const ELECTRON_PATH = path.join(__dirname, '..', '..', 'node_modules', '.bin', 'electron');

let electronProcess: ReturnType<typeof spawn> | null = null;

function startElectron(): void {
  if (electronProcess) {
    electronProcess.kill();
  }
  
  console.log('[HotReload] Starting Electron...');
  electronProcess = spawn(ELECTRON_PATH, ['.'], {
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'development' },
  });

  electronProcess.on('close', (code) => {
    console.log(`[HotReload] Electron exited with code ${code}`);
  });
}

function main(): void {
  console.log('[HotReload] Watching for changes in:', DIST_PATH);
  console.log('[HotReload] Press Ctrl+C to stop');

  // Watch for changes in dist folder
  const watcher = watch(DIST_PATH, {
    ignored: /(^|[\/\\])\../,
    persistent: true,
    ignoreInitial: true,
  });

  watcher
    .on('change', (filePath) => {
      console.log(`[HotReload] File changed: ${path.relative(DIST_PATH, filePath)}`);
      console.log('[HotReload] Restarting Electron...');
      startElectron();
    })
    .on('add', (filePath) => {
      console.log(`[HotReload] File added: ${path.relative(DIST_PATH, filePath)}`);
    })
    .on('error', (error) => {
      console.error('[HotReload] Watch error:', error);
    });

  // Handle Ctrl+C
  process.on('SIGINT', () => {
    console.log('[HotReload] Stopping...');
    watcher.close();
    if (electronProcess) {
      electronProcess.kill();
    }
    process.exit(0);
  });

  // Start Electron initially
  startElectron();
}

main();
