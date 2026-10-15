import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  testIgnore: '**/preview/**',
  fullyParallel: true,
  retries: 0,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:3029', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 } } },
  ],
  webServer: [
    { command: 'node tests/support/backend-server.mjs', url: 'http://127.0.0.1:18029/health', reuseExistingServer: false },
    { command: 'node tests/support/frontend-server.mjs', url: 'http://127.0.0.1:3029', reuseExistingServer: false,
      env: { MES_BACKEND_URL: 'http://127.0.0.1:18029', MES_NEXT_DIST_DIR: '.next/issue30-tests' }, timeout: 120000 },
  ],
})
