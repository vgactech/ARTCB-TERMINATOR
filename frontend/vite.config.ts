import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend target for the dev proxy. Defaults to the Guardian API port used by
// start_guardian.sh (8002). Override with VITE_API_PROXY to match a custom port.
const apiProxy = process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8002'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': apiProxy,
    },
  },
})
