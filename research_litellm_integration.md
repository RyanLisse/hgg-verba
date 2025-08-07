# LiteLLM Architecture and Integration Research

**Generated:** 2025-08-07 | **Sources:** 50+ documentation snippets, release notes, and integration guides

## Quick Reference

**Key Points:**

- LiteLLM v1.74.15+ supports 100+ LLM providers with unified OpenAI-compatible API
- Latest models: GPT-4.1 (1M context), Claude 4 Sonnet/Opus, Gemini 2.5 Flash/Pro
- Built-in async/streaming support perfect for FastAPI integration
- Comprehensive callback system for PostgreSQL observability and logging
- Cost tracking, error handling, and fallback mechanisms included

## Overview

LiteLLM serves as a universal gateway for Large Language Models, providing a unified interface to 100+ providers including OpenAI, Anthropic, Google, and local models via Ollama. For Verba's RAG application, LiteLLM offers seamless provider switching, built-in observability, and PostgreSQL integration patterns that align perfectly with the existing architecture.

## Implementation Details

### FastAPI Integration Patterns

**Async Completion Support**

```python
import litellm
from fastapi import FastAPI
from typing import AsyncGenerator

app = FastAPI()

async def generate_response(messages: list) -> AsyncGenerator[str, None]:
    """Stream responses from any LLM provider"""
    response = await litellm.acompletion(
        model="gpt-4.1",  # or claude-4-sonnet, gemini-2.5-pro
        messages=messages,
        stream=True,
        temperature=0.7
    )
    
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    return StreamingResponse(
        generate_response(request.messages),
        media_type="text/plain"
    )
```

**WebSocket Streaming for Verba**

```python
from fastapi import WebSocket
import asyncio

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        data = await websocket.receive_json()
        
        response = await litellm.acompletion(
            model=data.get("model", "gpt-4.1"),
            messages=data["messages"],
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                await websocket.send_json({
                    "type": "content",
                    "data": chunk.choices[0].delta.content
                })
        
        await websocket.send_json({"type": "done"})
```

### PostgreSQL Observability Integration

**Custom PostgreSQL Callback**

```python
import asyncpg
from typing import Dict, Any
from datetime import datetime

class PostgreSQLCallback:
    def __init__(self, db_url: str):
        self.db_url = db_url
        
    async def log_completion(
        self,
        kwargs: Dict[str, Any],
        completion_response: Any,
        start_time: float,
        end_time: float
    ):
        """Log LLM interactions to PostgreSQL"""
        conn = await asyncpg.connect(self.db_url)
        
        try:
            await conn.execute("""
                INSERT INTO llm_interactions (
                    timestamp, model, provider, messages, response,
                    tokens_used, cost, duration_ms, user_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                datetime.now(),
                kwargs.get("model"),
                self._extract_provider(kwargs.get("model")),
                str(kwargs.get("messages")),
                str(completion_response.choices[0].message.content),
                completion_response.usage.total_tokens,
                kwargs.get("response_cost", 0),
                (end_time - start_time) * 1000,
                kwargs.get("user_id")
            )
        finally:
            await conn.close()
    
    def _extract_provider(self, model: str) -> str:
        """Extract provider from model string"""
        if model.startswith("gpt-"):
            return "openai"
        elif model.startswith("claude-"):
            return "anthropic"
        elif model.startswith("gemini-"):
            return "google"
        return "unknown"

# Initialize callback
postgres_callback = PostgreSQLCallback("postgresql://user:pass@localhost:5432/verba")
litellm.success_callback = [postgres_callback.log_completion]
```

### Model Configuration for Verba

**Comprehensive Provider Setup**

```python
# litellm_config.py
LITELLM_MODELS = {
    "openai": [
        {
            "model_name": "gpt-4.1",
            "litellm_params": {
                "model": "gpt-4.1",
                "max_tokens": 4096,
                "temperature": 0.7
            }
        },
        {
            "model_name": "gpt-4.1-mini",
            "litellm_params": {
                "model": "gpt-4.1-mini",
                "max_tokens": 16384
            }
        }
    ],
    "anthropic": [
        {
            "model_name": "claude-4-sonnet",
            "litellm_params": {
                "model": "claude-4-sonnet-20250514",
                "max_tokens": 4096
            }
        }
    ],
    "google": [
        {
            "model_name": "gemini-2.5-pro",
            "litellm_params": {
                "model": "gemini-2.5-pro",
                "max_tokens": 8192
            }
        }
    ]
}

# Environment configuration
import os
os.environ["OPENAI_API_KEY"] = "your-key"
os.environ["ANTHROPIC_API_KEY"] = "your-key" 
os.environ["GOOGLE_API_KEY"] = "your-key"
```

### Error Handling and Fallbacks

**Robust Error Handling Pattern**

```python
from litellm.exceptions import RateLimitError, APIError
import asyncio

async def generate_with_fallback(
    messages: list,
    primary_model: str = "gpt-4.1",
    fallback_models: list = ["claude-4-sonnet", "gemini-2.5-pro"]
):
    """Generate response with automatic fallback"""
    models_to_try = [primary_model] + fallback_models
    
    for model in models_to_try:
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                timeout=30
            )
            return response
            
        except RateLimitError:
            if model != models_to_try[-1]:
                await asyncio.sleep(1)  # Brief pause before fallback
                continue
            raise
            
        except APIError as e:
            if model != models_to_try[-1]:
                continue
            raise
    
    raise Exception("All models failed")
```

### Cost Tracking Integration

**Built-in Cost Monitoring**

```python
import litellm

def cost_tracking_callback(kwargs, completion_response, start_time, end_time):
    """Track costs for budget management"""
    cost = kwargs.get("response_cost", 0)
    model = kwargs.get("model")
    user_id = kwargs.get("metadata", {}).get("user_id")
    
    # Log to PostgreSQL for Verba's budget tracking
    asyncio.create_task(log_usage_cost(user_id, model, cost))

litellm.success_callback = [cost_tracking_callback]

async def log_usage_cost(user_id: str, model: str, cost: float):
    """Log usage costs to database"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO usage_costs (user_id, model, cost, timestamp)
            VALUES ($1, $2, $3, $4)
        """, user_id, model, cost, datetime.now())
    finally:
        await conn.close()
```

## Important Considerations

**Warnings:**

- Rate limiting varies significantly between providers - implement exponential backoff
- Context window limits differ: GPT-4.1 (1M tokens), Claude-4 (200K), Gemini-2.5 (1M)
- Cost variations can be 10x between providers - monitor usage closely
- Streaming responses require proper error handling for connection drops
- PostgreSQL callback functions must be async-compatible for best performance

## Resources

**References:**

- [LiteLLM Documentation](https://docs.litellm.ai/) - Comprehensive API reference
- [Callback System Guide](https://docs.litellm.ai/docs/observability/callbacks) - Integration patterns
- [Provider Support Matrix](https://docs.litellm.ai/docs/providers) - All supported models
- [FastAPI Integration Examples](https://github.com/BerriAI/litellm/tree/main/cookbook) - Real-world patterns
- [PostgreSQL Observability](https://docs.litellm.ai/docs/proxy/db_info) - Database schema details
- [Release Notes v1.74.15](https://docs.litellm.ai/release_notes) - Latest features and fixes

## Verba-Specific Integration Recommendations

### 1. Generator Component Integration

Replace existing generators with unified LiteLLM approach:

```python
# goldenverba/components/generation/LiteLLMUnifiedGenerator.py
from litellm import acompletion
from typing import AsyncGenerator

class LiteLLMUnifiedGenerator(Generator):
    def __init__(self):
        super().__init__()
        self.name = "LiteLLMUnified"
        self.requires_env = ["LITELLM_MODEL"]
    
    async def generate(
        self, 
        messages: List[Message],
        context: str = "",
        conversation_id: str = ""
    ) -> AsyncGenerator[str, None]:
        model = os.getenv("LITELLM_MODEL", "gpt-4.1")
        
        response = await acompletion(
            model=model,
            messages=self._format_messages(messages, context),
            stream=True,
            metadata={"conversation_id": conversation_id}
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

### 2. Embedding Component Integration

Replace existing embedders with unified LiteLLM approach:

```python
# goldenverba/components/embedding/LiteLLMUnifiedEmbedder.py
from litellm import aembedding
from typing import List
import numpy as np

class LiteLLMUnifiedEmbedder(Embedding):
    def __init__(self):
        super().__init__()
        self.name = "LiteLLMUnified"
        self.requires_env = ["LITELLM_EMBEDDING_MODEL"]
        self.dimensions = self._get_model_dimensions()
    
    async def embed(
        self,
        texts: List[str],
        batch_size: int = 100,
        **kwargs
    ) -> List[List[float]]:
        """Embed texts using LiteLLM unified interface"""
        model = os.getenv("LITELLM_EMBEDDING_MODEL", "text-embedding-3-large")
        
        # Process in batches for better performance
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = await aembedding(
                model=model,
                input=batch,
                **self._get_provider_params()
            )
            
            # Extract embeddings from response
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
            
        return all_embeddings
    
    def _get_provider_params(self) -> dict:
        """Get provider-specific parameters"""
        model = os.getenv("LITELLM_EMBEDDING_MODEL", "text-embedding-3-large")
        params = {}
        
        if "cohere" in model:
            params["input_type"] = "search_document"
        elif "voyage" in model:
            # Voyage AI specific params if needed
            pass
        elif "text-embedding-3" in model:
            # OpenAI embedding-3 models support dimensions
            dimensions = os.getenv("LITELLM_EMBEDDING_DIMENSIONS")
            if dimensions:
                params["dimensions"] = int(dimensions)
                
        return params
    
    def _get_model_dimensions(self) -> int:
        """Get embedding dimensions for the current model"""
        model = os.getenv("LITELLM_EMBEDDING_MODEL", "text-embedding-3-large")
        
        # Dimension mapping for common models
        dimension_map = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
            "embed-english-v3.0": 1024,
            "voyage-3-large": 1024,
            "voyage-3": 1024,
            "mistral-embed": 1024,
            "textembedding-gecko": 768,
            "text-embedding-004": 768
        }
        
        # Extract model name without provider prefix
        clean_model = model.split("/")[-1] if "/" in model else model
        return dimension_map.get(clean_model, 1536)  # Default to 1536
    
    def get_config(self) -> dict:
        """Return configuration for frontend"""
        return {
            "Embedding Model": {
                "type": "text",
                "value": os.getenv("LITELLM_EMBEDDING_MODEL", "text-embedding-3-large"),
                "description": "LiteLLM embedding model (e.g., text-embedding-3-large, cohere/embed-english-v3.0)"
            },
            "Batch Size": {
                "type": "number", 
                "value": 100,
                "description": "Number of texts to process in each batch"
            },
            "Dimensions": {
                "type": "number",
                "value": self.dimensions,
                "description": "Embedding vector dimensions (auto-detected)"
            }
        }

# Supported embedding models configuration
LITELLM_EMBEDDING_MODELS = {
    "openai": [
        "text-embedding-3-large",     # 3072 dimensions, $0.13/1M tokens
        "text-embedding-3-small",     # 1536 dimensions, $0.02/1M tokens  
        "text-embedding-ada-002"      # 1536 dimensions, $0.10/1M tokens
    ],
    "cohere": [
        "embed-english-v3.0",         # 1024 dimensions
        "embed-multilingual-v3.0",    # 1024 dimensions
        "embed-english-light-v3.0"    # 384 dimensions
    ],
    "voyage": [
        "voyage/voyage-3.5",          # 1024 dimensions, latest model
        "voyage/voyage-3-large",      # 1024 dimensions
        "voyage/voyage-code-3",       # 1024 dimensions, code-optimized
        "voyage/voyage-finance-2",    # 1024 dimensions, finance-optimized
        "voyage/voyage-law-2"         # 1024 dimensions, legal-optimized
    ],
    "google": [
        "gemini/text-embedding-004",  # 768 dimensions
        "vertex_ai/textembedding-gecko" # 768 dimensions
    ],
    "mistral": [
        "mistral/mistral-embed"       # 1024 dimensions
    ],
    "bedrock": [
        "bedrock/amazon.titan-embed-text-v2:0",  # 1024 dimensions
        "bedrock/cohere.embed-english-v3"        # 1024 dimensions
    ]
}
```

### 3. PostgreSQL Integration with Verba Schema

Extend existing database schema:

```sql
-- Add to goldenverba/components/database_schema.sql
CREATE TABLE IF NOT EXISTS llm_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    messages JSONB NOT NULL,
    response TEXT,
    tokens_used INTEGER,
    cost DECIMAL(10, 6),
    duration_ms FLOAT,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_llm_interactions_conversation_id ON llm_interactions(conversation_id);
CREATE INDEX idx_llm_interactions_timestamp ON llm_interactions(timestamp);
CREATE INDEX idx_llm_interactions_model ON llm_interactions(model);
```

### 4. Environment Configuration

Update `.env.example`:

```bash
# LiteLLM Configuration
LITELLM_MODEL=gpt-4.1
LITELLM_EMBEDDING_MODEL=text-embedding-3-large
LITELLM_FALLBACK_MODELS=claude-4-sonnet,gemini-2.5-pro
LITELLM_MAX_TOKENS=4096
LITELLM_TEMPERATURE=0.7
LITELLM_EMBEDDING_DIMENSIONS=3072

# Provider API Keys (choose your providers)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
VOYAGE_API_KEY=your-voyage-key
COHERE_API_KEY=your-cohere-key

# Observability
LITELLM_LOG_TO_DB=true
LITELLM_TRACK_COSTS=true
```

## Metadata

**Research Details:**

- Research date: 2025-08-07
- Confidence: high
- Version checked: LiteLLM v1.74.15+, GPT-4.1, Claude 4, Gemini 2.5
- Integration complexity: medium
- Recommended approach: Replace existing generators with unified LiteLLM implementation
