const { chromium } = require('playwright');

async function testEmbedderSelection() {
  console.log('Starting Simple Embedder Test...');
  
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    // Navigate to the application
    console.log('1. Navigating to http://localhost:3000');
    await page.goto('http://localhost:3000');
    console.log('   ✓ Page loaded');
    
    // Wait for initial load
    await page.waitForTimeout(3000);
    
    // Look for the Chat button and click it
    console.log('2. Looking for Chat button...');
    const chatLink = await page.locator('a[href="/"], button').filter({ hasText: 'Chat' }).first();
    if (await chatLink.isVisible()) {
      await chatLink.click();
      console.log('   ✓ Clicked Chat');
    }
    
    await page.waitForTimeout(2000);
    
    // Look for config/settings icon or button
    console.log('3. Looking for Config button...');
    // Try different selectors for the config button
    const configButton = await page.locator('button').filter({ hasText: /config|setting/i }).first();
    if (await configButton.isVisible()) {
      await configButton.click();
      console.log('   ✓ Opened config');
    } else {
      // Try to find by role or icon
      const iconButton = await page.locator('button:has(svg)').nth(1);
      if (await iconButton.isVisible()) {
        await iconButton.click();
        console.log('   ✓ Opened config via icon');
      }
    }
    
    await page.waitForTimeout(2000);
    
    // Look for Embedder section
    console.log('4. Looking for Embedder section...');
    const embedderText = await page.locator('text=Embedder').first();
    if (await embedderText.isVisible()) {
      console.log('   ✓ Found Embedder section');
      
      // Find the dropdown button in the Embedder section
      const embedderDropdown = await page.locator('div:has-text("Embedder") button:has(svg)').first();
      if (await embedderDropdown.isVisible()) {
        const currentEmbedder = await embedderDropdown.textContent();
        console.log('   Current embedder:', currentEmbedder);
        
        await embedderDropdown.click();
        console.log('   ✓ Opened dropdown');
        
        await page.waitForTimeout(1000);
        
        // Select a different embedder
        const embedderOption = await page.locator('li a').filter({ hasText: 'OpenAIEmbedder' }).first();
        if (await embedderOption.isVisible()) {
          await embedderOption.click();
          console.log('   ✓ Selected OpenAIEmbedder');
        }
        
        await page.waitForTimeout(1000);
        
        // Save the configuration
        console.log('5. Saving configuration...');
        const saveButton = await page.locator('button').filter({ hasText: /save.*config/i }).first();
        if (await saveButton.isVisible()) {
          await saveButton.click();
          console.log('   ✓ Clicked Save Config');
          
          // Wait for save to complete
          await page.waitForTimeout(3000);
          
          // Check the current selection
          const updatedEmbedder = await embedderDropdown.textContent();
          console.log('   Updated embedder:', updatedEmbedder);
          
          if (updatedEmbedder.includes('OpenAIEmbedder')) {
            console.log('   ✓ SUCCESS: Embedder changed successfully!');
          }
        }
      }
    }
    
    // Take screenshot
    await page.screenshot({ path: 'embedder-test-final.png' });
    console.log('\nTest completed! Screenshot saved as embedder-test-final.png');
    
  } catch (error) {
    console.error('Test error:', error.message);
    await page.screenshot({ path: 'embedder-test-error.png' });
  } finally {
    await browser.close();
  }
}

// Run the test
testEmbedderSelection().catch(console.error);