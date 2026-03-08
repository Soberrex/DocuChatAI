import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor bundles for better caching & smaller initial load
          'vendor-react': ['react', 'react-dom'],
          'vendor-charts': ['recharts'],
          'vendor-motion': ['framer-motion'],
          'vendor-ui': ['lucide-react', '@mui/material', '@emotion/react', '@emotion/styled'],
        },
      },
    },
    // Target modern browsers for smaller bundles
    target: 'esnext',
    // Reduce chunk size warnings
    chunkSizeWarningLimit: 600,
  },
})
