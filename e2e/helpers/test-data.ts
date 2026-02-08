/**
 * Generate unique test data to avoid conflicts across test runs
 */

export function generateOrgName(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `E2ETest Org ${timestamp}-${random}`;
}

export function generateEmail(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `e2e-${timestamp}-${random}@test.voiceobs.com`;
}
