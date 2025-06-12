const { chromium } = require('playwright');

async function testEmbedderSelection() {
  console.log('Starting Embedder Selection Test...');
  
  const browser = await chromium.launch({ 
    headless: false, // Set to true for CI/CD
    slowMo: 500 // Slow down for visibility
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Navigate to the application
    console.log('1. Navigating to http://localhost:3000');
    await page.goto('http://localhost:3000', { waitUntil: 'domcontentloaded', timeout: 60000 });
    
    // Wait for the page to load
    await page.waitForTimeout(3000);
    
    // Click on the Chat tab/button
    console.log('2. Looking for Chat interface...');
    const chatButton = await page.getByText('Chat', { exact: false }).first();
    if (chatButton) {
      await chatButton.click();
      console.log('   ✓ Clicked on Chat');
    }
    
    // Wait for chat interface to load
    await page.waitForTimeout(2000);
    
    // Look for settings/config button (usually a gear icon or "Config" text)
    console.log('3. Looking for Settings/Config button...');
    const configButton = await page.locator('button').filter({ hasText: /config|settings/i }).first();
    if (!configButton) {
      // Try to find by icon (IoSettingsSharp is used in the code)
      const iconButton = await page.locator('button svg').first();
      if (iconButton) {
        await iconButton.click();
      }
    } else {
      await configButton.click();
    }
    console.log('   ✓ Opened configuration panel');
    
    await page.waitForTimeout(2000);
    
    // Find the Embedder dropdown
    console.log('4. Looking for Embedder dropdown...');
    const embedderSection = await page.locator('text=Embedder').first();
    if (embedderSection) {
      // Click on the dropdown button near the Embedder text
      const dropdownButton = await page.locator('button').filter({ has: page.locator('text=Embedder') }).first();
      if (!dropdownButton) {
        // Alternative: find button in the same parent as Embedder text
        const embedderDropdown = await page.locator('div:has-text("Embedder") button').first();
        await embedderDropdown.click();
      } else {
        await dropdownButton.click();
      }
      console.log('   ✓ Opened Embedder dropdown');
    }
    
    await page.waitForTimeout(1000);
    
    // Select a different embedder (e.g., "OpenAIEmbedder")
    console.log('5. Selecting OpenAIEmbedder...');
    const embedderOption = await page.locator('text=OpenAIEmbedder').first();
    if (embedderOption) {
      await embedderOption.click();
      console.log('   ✓ Selected OpenAIEmbedder');
    }
    
    await page.waitForTimeout(1000);
    
    // Find and click the Save Config button
    console.log('6. Looking for Save Config button...');
    const saveButton = await page.locator('button').filter({ hasText: /save.*config/i }).first();
    if (saveButton) {
      await saveButton.click();
      console.log('   ✓ Clicked Save Config');
    }
    
    // Wait for save to complete
    await page.waitForTimeout(3000);
    
    // Check for success message
    console.log('7. Checking for success message...');
    const successMessage = await page.locator('text=/success|saved/i').first();
    if (successMessage) {
      const messageText = await successMessage.textContent();
      console.log('   ✓ Success message:', messageText);
    }
    
    // Refresh the page to verify persistence
    console.log('8. Refreshing page to verify persistence...');
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    
    // Navigate back to config
    const chatButtonAfterRefresh = await page.getByText('Chat', { exact: false }).first();
    if (chatButtonAfterRefresh) {
      await chatButtonAfterRefresh.click();
    }
    await page.waitForTimeout(2000);
    
    const configButtonAfterRefresh = await page.locator('button').filter({ hasText: /config|settings/i }).first();
    if (configButtonAfterRefresh) {
      await configButtonAfterRefresh.click();
    }
    await page.waitForTimeout(2000);
    
    // Check if OpenAIEmbedder is still selected
    console.log('9. Verifying embedder selection persisted...');
    const selectedEmbedder = await page.locator('div:has-text("Embedder") button').first();
    if (selectedEmbedder) {
      const embedderText = await selectedEmbedder.textContent();
      if (embedderText.includes('OpenAIEmbedder')) {
        console.log('   ✓ SUCCESS: Embedder selection persisted!');
        console.log('   Selected embedder:', embedderText);
      } else {
        console.log('   ✗ FAIL: Embedder selection did not persist');
        console.log('   Current embedder:', embedderText);
      }
    }
    
    console.log('\nTest completed!');
    
  } catch (error) {
    console.error('Test failed with error:', error);
  } finally {
    // Take a screenshot for debugging
    await page.screenshot({ path: 'embedder-test-result.png' });
    console.log('Screenshot saved as embedder-test-result.png');
    
    // Close browser
    await browser.close();
  }
}

// Run the test
testEmbedderSelection().catch(console.error);