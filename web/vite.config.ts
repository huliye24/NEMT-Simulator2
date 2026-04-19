import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Cloudflare Pages 部署配置
export default defineConfig({
  plugins: [react()],
  base: '/',  // Cloudflare Pages 默认路径
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // 优化构建
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
