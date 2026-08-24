/**
 * NEMT Simulator - Dependency Check Script
 *
 * Verifies that all required dependencies and resources are in place
 * before starting the Electron application.
 *
 * Usage:
 *   node scripts/check-deps.js
 *
 * Exit codes:
 *   0 - All checks passed
 *   1 - One or more checks failed
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get the electron directory (parent of scripts)
const ELECTRON_DIR = path.resolve(__dirname, '..');
// For cross-references to sibling directories like web/
const ROOT_DIR = path.resolve(ELECTRON_DIR, '..');

// Colors for output
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';

function log(message, status) {
  const prefix = status === 'ok'
    ? `${GREEN}[OK]${RESET}`
    : status === 'warn'
    ? `${YELLOW}[WARN]${RESET}`
    : `${RED}[FAIL]${RESET}`;
  console.log(`${prefix} ${message}`);
}

function checkFile(filePath, description) {
  // Check relative to ELECTRON_DIR (electron/)
  const fullPath = path.resolve(ELECTRON_DIR, filePath);
  if (fs.existsSync(fullPath)) {
    log(`${description}: ${filePath}`, 'ok');
    return true;
  } else {
    log(`${description}: ${filePath} (NOT FOUND)`, 'fail');
    return false;
  }
}

function checkDir(dirPath, description) {
  // Check relative to ELECTRON_DIR (electron/)
  const fullPath = path.resolve(ELECTRON_DIR, dirPath);
  if (fs.existsSync(fullPath)) {
    log(`${description}: ${dirPath}`, 'ok');
    return true;
  } else {
    log(`${description}: ${dirPath} (NOT FOUND)`, 'fail');
    return false;
  }
}

function checkCommand(command, description) {
  try {
    execSync(command, { stdio: 'ignore' });
    log(`${description}: ${command}`, 'ok');
    return true;
  } catch {
    log(`${description}: ${command} (NOT AVAILABLE)`, 'warn');
    return false;
  }
}

async function checkGateway() {
  try {
    const http = require('http');
    return new Promise((resolve) => {
      const req = http.get('http://localhost:8080/health', { timeout: 3000 }, (res) => {
        log('Go Gateway: http://localhost:8080 (CONNECTED)', 'ok');
        resolve(true);
      });
      req.on('error', () => {
        log('Go Gateway: http://localhost:8080 (NOT RUNNING)', 'warn');
        resolve(false);
      });
      req.on('timeout', () => {
        req.destroy();
        log('Go Gateway: http://localhost:8080 (TIMEOUT)', 'warn');
        resolve(false);
      });
    });
  } catch {
    log('Go Gateway: http://localhost:8080 (NOT AVAILABLE)', 'warn');
    return false;
  }
}

async function main() {
  console.log('='.repeat(50));
  console.log('NEMT Simulator - Dependency Check');
  console.log('='.repeat(50));
  console.log('');

  let allPassed = true;

  // 1. Check package.json
  console.log('[1] Checking package.json...');
  allPassed &= checkFile('package.json', 'Electron package.json');

  // 2. Check TypeScript compilation
  console.log('\n[2] Checking TypeScript configuration...');
  allPassed &= checkFile('tsconfig.json', 'TypeScript config');

  // 3. Check main process files
  console.log('\n[3] Checking main process files...');
  allPassed &= checkFile('src/main.ts', 'Main process entry');
  allPassed &= checkFile('src/main/window.ts', 'Window manager');
  allPassed &= checkFile('src/main/menu.ts', 'Menu manager');
  allPassed &= checkFile('src/main/tray.ts', 'Tray manager');
  allPassed &= checkFile('src/main/ipc.ts', 'IPC client');

  // 4. Check preload script
  console.log('\n[4] Checking preload script...');
  allPassed &= checkFile('src/preload.ts', 'Preload script');

  // 5. Check icons
  console.log('\n[5] Checking icons...');
  checkFile('build/icon.svg', 'App icon (SVG)');
  checkFile('build/icon.png', 'App icon (PNG)');

  // 6. Check node_modules
  console.log('\n[6] Checking dependencies...');
  allPassed &= checkDir('node_modules', 'Node modules');
  if (!allPassed) {
    log('Run: cd electron && npm install', 'warn');
  }

  // 7. Check web app
  console.log('\n[7] Checking web app...');
  checkDir('../web/src', 'Web source');
  checkFile('../web/package.json', 'Web package.json');

  // 8. Check compiled output
  console.log('\n[8] Checking compiled output...');
  checkFile('dist-electron/main.js', 'Compiled main.js');
  checkFile('dist-electron/preload.js', 'Compiled preload.js');

  // 9. Check Go Gateway
  console.log('\n[9] Checking Go Gateway...');
  const gatewayOk = await checkGateway();
  if (!gatewayOk) {
    log('Application will start in standalone mode', 'warn');
  }

  // 10. Check commands
  console.log('\n[10] Checking available commands...');
  checkCommand('node --version', 'Node.js');
  checkCommand('npm --version', 'npm');

  // Summary
  console.log('\n' + '='.repeat(50));
  if (allPassed) {
    log('All critical checks passed!', 'ok');
    console.log('\nYou can now run: npm run dev:electron');
  } else {
    log('Some checks failed. Please fix the issues above.', 'fail');
    process.exit(1);
  }
  console.log('='.repeat(50));
}

main().catch((err) => {
  console.error('Check script error:', err);
  process.exit(1);
});
