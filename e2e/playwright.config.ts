import { defineConfig, devices } from '@playwright/test';
// import * as dotenv from 'dotenv';

// // Load test environment variables
// dotenv.config({ path: '.env.test' });

export default defineConfig({
  testDir: './specs',
  fullyParallel: false, // Run tests serially to avoid org conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker to avoid conflicts
  reporter: 'html',

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
