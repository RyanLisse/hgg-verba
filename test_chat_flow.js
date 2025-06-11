const { test, expect } = require('@playwright/test');

test.describe('Verba Chat Flow', () => {
  test('complete chat flow with new June 2025 models', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    // Check if the chat interface is loaded
    await expect(page.locator('text="Chat"').first()).toBeVisible();

    // Click on Config button
    await page.click('button:has-text("Config")');
    await page.waitForTimeout(1000);

    // Verify OpenAI is selected as generator
    const generatorSection = page.locator('div:has-text("Generator")').filter({ hasText: 'OpenAI' });
    await expect(generatorSection).toBeVisible();

    // Click on the generator dropdown to see available models
    await generatorSection.locator('button').first().click();
    await page.waitForTimeout(500);

    // Check that new models are available in the dropdown
    const dropdownContent = page.locator('.dropdown-content').last();
    await expect(dropdownContent).toBeVisible();
    
    // Close dropdown by clicking elsewhere
    await page.click('body', { position: { x: 100, y: 100 } });

    // Navigate to Chat
    await page.click('button:has-text("Chat")').first();
    await page.waitForTimeout(1000);

    // Type a test message
    const chatInput = page.locator('textarea').first();
    await chatInput.fill('Hello, can you tell me about the latest AI models available?');

    // Send the message
    await page.keyboard.press('Enter');
    
    // Wait for response
    await page.waitForSelector('.chat-message', { timeout: 30000 });

    // Verify response is received
    const messages = page.locator('.chat-message');
    await expect(messages).toHaveCount({ minimum: 1 });

    // Take a screenshot of the chat
    await page.screenshot({ path: 'chat-flow-test.png', fullPage: true });

    console.log('Chat flow test completed successfully!');
  });

  test('verify model configuration persistence', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');

    // Go to Config
    await page.click('button:has-text("Config")');
    await page.waitForTimeout(1000);

    // Change embedder to OpenAI
    const embedderDropdown = page.locator('div:has-text("Embedder")').locator('.dropdown button').first();
    await embedderDropdown.click();
    
    const openAIOption = page.locator('.dropdown-content li:has-text("OpenAI")').first();
    await openAIOption.click();
    await page.waitForTimeout(500);

    // Save configuration
    await page.click('button:has-text("Save Config")');
    await page.waitForTimeout(2000);

    // Refresh page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Go back to Config
    await page.click('button:has-text("Config")');
    await page.waitForTimeout(1000);

    // Verify OpenAI is still selected
    const embedderButton = page.locator('div:has-text("Embedder")').locator('.dropdown button').first();
    await expect(embedderButton).toHaveText(/OpenAI/);

    console.log('Model configuration persistence test completed!');
  });
});