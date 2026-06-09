// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === 'production' ? '/static/frontend/' : '/',
  build: {
    outDir: '../staticfiles/frontend',
    emptyOutDir: true,
    manifest: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://192.168.190.130:8000',
        changeOrigin: true,
        headers: { 'Host': 'demo.localhost' }
      }
    }
  }
}))
