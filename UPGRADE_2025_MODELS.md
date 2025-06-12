# 2025 Model and API Updates

This document describes the updates made to support the latest 2025 models and APIs from OpenAI and Google.

## OpenAI Updates

### Updated Models (OpenAIGenerator.py)
- **GPT-4o mini** - Efficient model for simple tasks
- **GPT-4o** - Optimized GPT-4 model
- **GPT-4o-2024-11-20** - Latest stable GPT-4o release
- **o1** - New reasoning model
- **o1-mini** - Smaller reasoning model
- **o1-preview** - Preview of the o1 model

### Context Window
- Updated from 10,000 tokens to 128,000 tokens
- GPT-4o models support 128k tokens
- o1 models support 128k-200k tokens

### API Migration
- **Migrated from Chat Completions API to Responses API**
- New features available:
  - Built-in web search tool
  - Built-in file search tool
  - Better state management with `store=True`
  - Improved streaming support

### Configuration Options
- **Enable Web Search**: Checkbox to enable web search for up-to-date information
- **Enable File Search**: Checkbox to enable file search for document queries

### Embeddings (OpenAIEmbedder.py)
- Already supports latest models:
  - text-embedding-3-small
  - text-embedding-3-large

## Google Gemini Updates

### Updated Models (GeminiGenerator.py)
- **gemini-2.5-flash-preview-05-20** - Latest Gemini 2.5 Flash preview (default)
- **gemini-2.0-flash-exp** - Experimental Gemini 2.0 model
- **gemini-1.5-pro-002** - Latest stable Gemini 1.5 Pro
- **gemini-1.5-flash-002** - Fast, efficient model
- **gemini-1.5-pro-latest** - Latest preview version
- **gemini-1.5-flash-latest** - Latest flash preview

### API Migration
- **Migrated from Vertex AI to new google.genai client**
- Simpler authentication using `GOOGLE_API_KEY` instead of service account
- More streamlined API with better async support
- Direct model access without regional endpoints

### Context Window
- Updated from 10,000 tokens to 1,000,000 tokens
- Gemini models support up to 2M tokens

### Configuration
- Added model selection dropdown for easy switching between models
- Simplified authentication process

## Usage

The models will automatically appear in the Verba UI dropdown when configuring the generator. No additional code changes are required for users.

### OpenAI Example
```python
# The model selection is now available in the UI
# Default is "gpt-4o-mini" for efficiency
```

### Google Gemini Example
```python
# The model selection is now available in the UI
# Default is "gemini-1.5-pro-002" for best performance
```

## Environment Variables

### OpenAI
- `OPENAI_API_KEY` - No change, still required
- `OPENAI_BASE_URL` - Optional, for custom endpoints

### Google
- **NEW**: `GOOGLE_API_KEY` - Required for the new google.genai client
- **DEPRECATED**: `GOOGLE_CLOUD_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS` - No longer needed

## Installation

### Install/Update Dependencies

For Google support:
```bash
pip install goldenverba[google]
# or
pip install google-genai
```

For development:
```bash
pip install -e ".[google]"
```

## Anthropic Updates

### Updated Models (AnthropicGenerator.py)
- **claude-4-opus-20250514** - Most capable Claude 4 model
- **claude-4-sonnet-20250514** - Balanced performance and cost (default)
- **claude-4-haiku-20250514** - Fast and efficient
- **claude-3.5-sonnet-20241022** - Previous generation for compatibility
- **claude-3.5-haiku-20241022** - Previous generation fast model

### API Migration
- **Migrated to latest Anthropic SDK**
- Uses async client for better performance
- Proper streaming support with new event types
- Added configuration options:
  - Temperature control (0.0-1.0)
  - Analysis tool for complex reasoning

### Context Window
- Updated from 10,000 tokens to 200,000 tokens
- Claude 4 models support significantly larger contexts

## Breaking Changes

None. The updates maintain backward compatibility while adding new model options.