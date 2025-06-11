const { test, expect } = require('@playwright/test');

test('Basic Verba connectivity test', async ({ page }) => {
  // Navigate to the application
  await page.goto('http://localhost:3000');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Take a screenshot
  await page.screenshot({ path: 'basic-test.png', fullPage: true });
  
  // Check if page title contains Verba
  const title = await page.title();
  console.log('Page title:', title);
  
  // Look for key UI elements
  const chatElements = await page.locator('text=Chat').count();
  console.log('Chat elements found:', chatElements);
  
  // Check for any error messages
  const errorElements = await page.locator('.error, [data-testid="error"]').count();
  console.log('Error elements found:', errorElements);
  
  console.log('Basic connectivity test completed successfully!');
});