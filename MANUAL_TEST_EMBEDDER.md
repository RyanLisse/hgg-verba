# Manual Test for Embedder Selection Persistence

## Test Steps

1. **Open the Application**
   - Navigate to http://localhost:3000 in your browser
   - The application should load successfully

2. **Go to Chat Interface**
   - Click on the "Chat" tab/button in the navigation

3. **Open Configuration**
   - Look for a settings/config button (might be a gear icon ⚙️)
   - Click it to open the configuration panel

4. **Find Embedder Section**
   - You should see an "Embedder" section with a dropdown
   - Note the currently selected embedder

5. **Change Embedder**
   - Click on the Embedder dropdown
   - Select a different embedder (e.g., if "WeaviateEmbedder" is selected, choose "OpenAIEmbedder")
   - The dropdown should update to show your selection

6. **Save Configuration**
   - Click the "Save Config" button
   - You should see a success message like "Config saved successfully"

7. **Verify Persistence**
   - Refresh the page (F5 or Cmd+R)
   - Go back to Chat → Configuration
   - Check if the Embedder dropdown still shows your previously selected embedder

## Expected Result
- The embedder selection should persist after saving and refreshing the page
- You should see console logs in the browser developer tools showing the selection (F12 → Console)

## What Was Fixed
1. **State Management**: Fixed React state updates using deep cloning instead of shallow copying
2. **Save Function**: Added proper error handling and automatic config refresh after save
3. **API Response**: Ensured the configuration is properly verified after saving

## Troubleshooting
- If the embedder doesn't persist, check the browser console for errors
- Check the backend logs for any API errors
- Ensure both frontend and backend servers are running properly