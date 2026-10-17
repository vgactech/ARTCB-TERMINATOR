import { defineConfig } from 'vitest/config'

// Standalone config so tests do not load the app's Vite plugins (react, tailwind).
export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
