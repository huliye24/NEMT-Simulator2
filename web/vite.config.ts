import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

// Cloudflare Pages 部署配置
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-redirects',
      writeBundle() {
        // 复制 _redirects 文件到 dist 目录 (Cloudflare Pages SPA 支持)
        const redirectsPath = path.join(__dirname, 'public', '_redirects')
        if (fs.existsSync(redirectsPath)) {
          fs.copyFileSync(redirectsPath, path.join(__dirname, 'dist', '_redirects'))
        } else {
          // 如果不存在，创建一个默认的重定向规则
          const distRedirects = path.join(__dirname, 'dist', '_redirects')
          fs.writeFileSync(distRedirects, '/*    /index.html   200\n')
        }
      }
    }
  ],
  base: '/',
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['chart.js', 'react-chartjs-2']
        }
      }
    }
  }
})
