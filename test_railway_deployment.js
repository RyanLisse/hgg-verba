const { test, expect } = require('@playwright/test');

test.describe('Railway Verba Deployment Tests', () => {
  const RAILWAY_URL = 'https://hgg-verba-production.up.railway.app';

  test('should load the main page successfully', async ({ page }) => {
    console.log('Testing Railway deployment at:', RAILWAY_URL);
    
    // Navigate to the Railway deployment
    await page.goto(RAILWAY_URL);
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check if the page title contains "Verba"
    await expect(page).toHaveTitle(/Verba/);
    
    // Take a screenshot
    await page.screenshot({ path: 'railway-homepage.png', fullPage: true });
    
    console.log('✅ Main page loaded successfully');
  });

  test('should have working API health endpoint', async ({ page }) => {
    // Test the API health endpoint directly
    const response = await page.request.get(`${RAILWAY_URL}/api/health`);
    expect(response.status()).toBe(200);
    
    const healthData = await response.json();
    console.log('Health check response:', healthData);
    
    expect(healthData).toHaveProperty('status');
    console.log('✅ API health endpoint working');
  });

  test('should load the chat interface', async ({ page }) => {
    await page.goto(RAILWAY_URL);
    await page.waitForLoadState('networkidle');
    
    // Look for chat-related elements
    const chatElements = [
      'input[placeholder*="message"]',
      'textarea[placeholder*="message"]',
      'button[type="submit"]',
      '[data-testid="chat-input"]',
      '.chat-input',
      '#chat-input'
    ];
    
    let foundChatElement = false;
    for (const selector of chatElements) {
      try {
        await page.waitForSelector(selector, { timeout: 5000 });
        foundChatElement = true;
        console.log(`✅ Found chat element: ${selector}`);
        break;
      } catch (e) {
        // Continue to next selector
      }
    }
    
    // Take a screenshot of the interface
    await page.screenshot({ path: 'railway-chat-interface.png', fullPage: true });
    
    if (!foundChatElement) {
      console.log('⚠️  No specific chat input found, but page loaded successfully');
    }
  });

  test('should check for OpenAI configuration options', async ({ page }) => {
    await page.goto(RAILWAY_URL);
    await page.waitForLoadState('networkidle');
    
    // Look for settings or configuration elements
    const configElements = [
      'button[aria-label*="settings"]',
      'button[aria-label*="config"]',
      '[data-testid="settings"]',
      '.settings',
      'button:has-text("Settings")',
      'button:has-text("Config")',
      'select',
      'option'
    ];
    
    let foundConfigElement = false;
    for (const selector of configElements) {
      try {
        const elements = await page.locator(selector).all();
        if (elements.length > 0) {
          foundConfigElement = true;
          console.log(`✅ Found config element: ${selector} (${elements.length} elements)`);
          
          // If it's a select or option, check for OpenAI
          if (selector.includes('select') || selector.includes('option')) {
            const text = await elements[0].textContent();
            if (text && text.toLowerCase().includes('openai')) {
              console.log('✅ Found OpenAI option in configuration');
            }
          }
        }
      } catch (e) {
        // Continue to next selector
      }
    }
    
    // Check page content for OpenAI mentions
    const pageContent = await page.content();
    if (pageContent.toLowerCase().includes('openai')) {
      console.log('✅ OpenAI mentioned in page content');
    }
    
    // Take a screenshot
    await page.screenshot({ path: 'railway-config-check.png', fullPage: true });
    
    console.log(foundConfigElement ? '✅ Configuration elements found' : '⚠️  No specific config elements found');
  });

  test('should test API endpoints', async ({ page }) => {
    const endpoints = [
      '/api/health',
      '/api/get_config',
      '/api/get_status'
    ];
    
    for (const endpoint of endpoints) {
      try {
        const response = await page.request.get(`${RAILWAY_URL}${endpoint}`);
        console.log(`${endpoint}: ${response.status()}`);
        
        if (response.status() === 200) {
          const data = await response.json();
          console.log(`✅ ${endpoint} working:`, Object.keys(data));
        }
      } catch (e) {
        console.log(`❌ ${endpoint} failed:`, e.message);
      }
    }
  });

  test('should check console for errors', async ({ page }) => {
    const consoleMessages = [];
    const errors = [];
    
    page.on('console', msg => {
      consoleMessages.push(`${msg.type()}: ${msg.text()}`);
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto(RAILWAY_URL);
    await page.waitForLoadState('networkidle');
    
    // Wait a bit more to catch any delayed console messages
    await page.waitForTimeout(3000);
    
    console.log('\n=== Console Messages ===');
    consoleMessages.forEach(msg => console.log(msg));
    
    console.log('\n=== Errors Found ===');
    if (errors.length === 0) {
      console.log('✅ No console errors found');
    } else {
      errors.forEach(error => console.log(`❌ ${error}`));
    }
    
    // Take final screenshot
    await page.screenshot({ path: 'railway-final-state.png', fullPage: true });
  });
});
