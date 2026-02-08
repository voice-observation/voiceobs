# E2E Tests

End-to-end tests for voiceobs using Playwright.

## Setup

1. **Install dependencies:**
   ```bash
   cd e2e
   npm install
   npx playwright install chromium
   ```

2. **Configure test user:**
   ```bash
   cp .env.test.example .env.test
   # Edit .env.test and add your test user credentials
   ```

3. **Create test user in Supabase:**
   - Go to your Supabase dashboard
   - Create a new user with email/password
   - Use these credentials in `.env.test`

## Running Tests

**Prerequisites:** Frontend and backend must be running locally:
- Frontend: `cd ui && npm run dev` (port 3000)
- Backend: `cd .. && uv run uvicorn voiceobs.server.app:app --reload` (port 8765)

**Run all tests:**
```bash
npm test
```

**Run specific test suite:**
```bash
npm run test:auth       # Authentication tests
npm run test:org        # Organization tests
```

**Debug mode:**
```bash
npm run test:debug      # Step through tests with debugger
npm run test:ui         # Run with Playwright UI
npm run test:headed     # Run with browser visible
```

## Test Structure

```
e2e/
├── fixtures/           # Custom Playwright fixtures (auth)
├── helpers/            # Utilities (API client, test data)
├── pages/              # Page Object Model classes
├── specs/              # Test files
│   ├── auth.spec.ts
│   └── organization.spec.ts
└── playwright.config.ts
```

## Writing Tests

All tests should:
1. Use Page Object Model classes from `pages/`
2. Use `authenticatedPage` fixture for tests requiring auth
3. Clean up test data in `afterEach` hooks
4. Generate unique names with `generateOrgName()` from `helpers/test-data.ts`

Example:
```typescript
import { test, expect } from '../fixtures/auth.fixture';
import { SidebarPage } from '../pages/sidebar.page';
import { generateOrgName } from '../helpers/test-data';

test('should create organization', async ({ authenticatedPage }) => {
  const sidebar = new SidebarPage(authenticatedPage);
  const orgName = generateOrgName();

  await sidebar.createOrg(orgName);

  // Assertions...
});
```

## Troubleshooting

**Tests fail with "TEST_USER_EMAIL not set":**
- Make sure `.env.test` exists and has credentials

**Tests fail with connection errors:**
- Verify frontend (port 3000) and backend (port 8765) are running

**Auth tests fail:**
- Check that test user exists in Supabase and credentials are correct
- Delete `.auth/user.json` to force re-login

**Tests are flaky:**
- Check for hardcoded waits (`waitForTimeout`) and replace with proper assertions
- Ensure tests run serially (workers: 1 in playwright.config.ts)
