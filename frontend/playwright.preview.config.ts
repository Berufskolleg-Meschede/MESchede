import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/preview', testMatch: 'ui.spec.ts', workers: 1,
  use: { baseURL: 'http://127.0.0.1:3030', trace: 'retain-on-failure' },
  projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 } } }],
  webServer: { command: 'npm run dev:preview', url: 'http://127.0.0.1:3030', reuseExistingServer: false, timeout: 60000 },
})
