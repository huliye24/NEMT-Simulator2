/**
 * NEMT Simulator - AfterPack Script
 * 
 * This script runs after electron-builder packs the application.
 * It handles post-packaging tasks like:
 * - Setting file permissions
 * - Creating additional directories
 * - Copying resources
 */

const { execSync } = require('child_process');
const path = require('path');

exports.default = async function afterPack(context) {
  const { appOutDir, packager } = context;
  const platform = packager.platform.name;

  console.log(`AfterPack: Processing ${platform} build...`);

  // Create necessary directories
  const dirsToCreate = [
    'logs',
    'data',
    'cache',
  ];

  for (const dir of dirsToCreate) {
    try {
      const dirPath = path.join(appOutDir, dir);
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(`Created directory: ${dir}`);
      }
    } catch (error) {
      console.warn(`Failed to create directory ${dir}:`, error.message);
    }
  }

  // Platform-specific handling
  if (platform === 'mac') {
    // Set file permissions for gateway binary
    try {
      const gatewayPath = path.join(
        appOutDir,
        'Contents/Resources/gateway/gateway'
      );
      execSync(`chmod +x "${gatewayPath}"`, { stdio: 'ignore' });
    } catch (error) {
      console.warn('Failed to set gateway permissions:', error.message);
    }
  }

  if (platform === 'linux') {
    // Ensure gateway is executable
    try {
      const gatewayPath = path.join(
        appOutDir,
        'resources/gateway/gateway'
      );
      execSync(`chmod +x "${gatewayPath}"`, { stdio: 'ignore' });
    } catch (error) {
      console.warn('Failed to set gateway permissions:', error.message);
    }
  }

  console.log('AfterPack: Complete');
};

const fs = require('fs');
