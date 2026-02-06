import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/generate-video': 'http://localhost:8000',
      '/videos': 'http://localhost:8000',
    },
  },
})
