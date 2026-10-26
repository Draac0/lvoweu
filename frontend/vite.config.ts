import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // `@/components/X` instead of `../../components/X`. Mirrors "paths" in tsconfig.app.json.
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    // In development, send API calls to the FastAPI server (uv run uvicorn app.main:app).
    proxy: { '/api': 'http://localhost:8000' },
  },
})
