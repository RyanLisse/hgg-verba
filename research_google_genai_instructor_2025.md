# Google GenAI SDK & Instructor Integration Research 2025

_Generated: 2025-08-05 | Sources: 15+ official docs, migration guides, and implementation examples_

## 🚨 Critical Migration Notice

**URGENT**: The legacy `google-generativeai` package reaches End-of-Life on **August 31, 2025**. All projects must migrate to the new `google-genai` SDK to maintain support and access to latest features.

## 🎯 Quick Reference

<key-points>
- Legacy package EOL: August 31, 2025 - immediate migration required
- New unified SDK: `google-genai` supports both Gemini API and Vertex AI
- Instructor integration: Use `instructor.from_provider("google/gemini-2.5-flash")` or `instructor.from_genai()`
- Authentication: API key via `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variables
- Structured outputs: Native support with `response_mime_type` and `response_schema`
- Async support: Full async/await patterns with `client.aio` methods
- Streaming limitation: No streaming support with structured outputs/tools yet
</key-points>

## 📋 Overview

<summary>
Google's Generative AI ecosystem underwent major changes in late 2024/early 2025 with the introduction of the unified Google GenAI SDK. This new SDK replaces the legacy google-generativeai package and provides a consistent interface for both the Gemini Developer API and Vertex AI. The Instructor library has been updated to support structured outputs with the new SDK, offering robust Pydantic-based data extraction capabilities.
</summary>

## 🔧 Implementation Details

<details>
### Installation & Setup

#### New Google GenAI SDK

```bash
# Install the new unified SDK
pip install google-genai

# Install with Instructor integration
pip install "instructor[google-genai]"

# For development/testing
pip install google-genai[dev]
```

#### Environment Variables

```bash
# Primary authentication (choose one)
export GOOGLE_API_KEY="your-api-key-here"
export GEMINI_API_KEY="your-api-key-here"  # Alternative

# For Vertex AI usage
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

### Basic Usage Patterns

#### 1. Standard Content Generation

```python
from google import genai
from google.genai import types

# Initialize client (auto-detects API key from environment)
client = genai.Client()

# Simple generation
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Explain quantum computing in simple terms'
)
print(response.text)
```

#### 2. Async Operations

```python
import asyncio
from google import genai

async def generate_async():
    client = genai.Client()
    
    # Async generation
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents='Tell me about machine learning'
    )
    print(response.text)
    
    # Async streaming
    async for chunk in await client.aio.models.generate_content_stream(
        model='gemini-2.5-flash',
        contents='Write a story about AI'
    ):
        print(chunk.text, end='')

# Run async function
asyncio.run(generate_async())
```

#### 3. Structured Outputs (Native)

```python
from google import genai
from google.genai import types
from enum import Enum

class ResponseType(Enum):
    INFORMATIVE = 'informative'
    CREATIVE = 'creative'
    ANALYTICAL = 'analytical'

client = genai.Client()

# JSON structured output
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Analyze the benefits of renewable energy',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema={
            'type': 'OBJECT',
            'required': ['summary', 'benefits', 'challenges'],
            'properties': {
                'summary': {'type': 'STRING'},
                'benefits': {
                    'type': 'ARRAY',
                    'items': {'type': 'STRING'}
                },
                'challenges': {
                    'type': 'ARRAY', 
                    'items': {'type': 'STRING'}
                },
                'confidence_score': {'type': 'NUMBER'}
            }
        }
    )
)
```

#### 4. Enum-constrained Outputs

```python
from enum import Enum

class SentimentEnum(Enum):
    POSITIVE = 'positive'
    NEGATIVE = 'negative'
    NEUTRAL = 'neutral'

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='This product is amazing and works perfectly!',
    config={
        'response_mime_type': 'text/x.enum',
        'response_schema': SentimentEnum
    }
)
print(response.text)  # Returns: 'positive'
```

### Advanced Features

#### 1. Multimodal Inputs

```python
from google.genai import types

# Image + text input
contents = [
    types.Part.from_text('What do you see in this image?'),
    types.Part.from_uri(
        file_uri='gs://your-bucket/image.jpg',
        mime_type='image/jpeg'
    )
]

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=contents
)
```

#### 2. Function Calling

```python
import json

# Define function schema
weather_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name='get_weather',
            description='Get weather information for a location',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'location': types.Schema(type=types.Type.STRING),
                    'unit': types.Schema(type=types.Type.STRING, enum=['celsius', 'fahrenheit'])
                },
                required=['location']
            )
        )
    ]
)

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What\'s the weather like in Tokyo?',
    config=types.GenerateContentConfig(tools=[weather_tool])
)

# Handle function calls
if response.function_calls:
    for call in response.function_calls:
        if call.name == 'get_weather':
            # Execute function with call.args
            weather_data = get_weather(**call.args)
            
            # Return result to model
            function_response = types.Part.from_function_response(
                name=call.name,
                response={'result': weather_data}
            )
```

#### 3. Streaming with Context

```python
async def stream_with_context():
    client = genai.Client()
    
    # Maintain conversation context
    conversation = [
        types.Content(
            role='user',
            parts=[types.Part.from_text('Hello, I\'m working on a Python project')]
        ),
        types.Content(
            role='model',
            parts=[types.Part.from_text('Great! I\'d be happy to help with your Python project. What are you working on?')]
        ),
        types.Content(
            role='user', 
            parts=[types.Part.from_text('I need help with async programming')]
        )
    ]
    
    async for chunk in await client.aio.models.generate_content_stream(
        model='gemini-2.5-flash',
        contents=conversation
    ):
        print(chunk.text, end='')
```

### Instructor Integration Patterns

#### 1. Provider-based Integration (Recommended)

```python
import instructor
from pydantic import BaseModel, Field
from typing import List

class TechAnalysis(BaseModel):
    """Analysis of a technology topic."""
    summary: str = Field(description="Brief summary of the topic")
    key_points: List[str] = Field(description="Main points to understand")
    difficulty_level: str = Field(description="Beginner, Intermediate, or Advanced")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in analysis")

# Initialize Instructor client
client = instructor.from_provider("google/gemini-2.5-flash")

# Generate structured response
analysis = client.chat.completions.create(
    messages=[{
        "role": "user", 
        "content": "Analyze the concept of microservices architecture"
    }],
    response_model=TechAnalysis
)

print(f"Summary: {analysis.summary}")
print(f"Difficulty: {analysis.difficulty_level}")
print(f"Confidence: {analysis.confidence_score}")
```

#### 1.1. Alternative Providers

```python
# Cohere integration (good for prototyping with free tier)
cohere_client = instructor.from_provider("cohere/command-r-plus")

# Same usage pattern works across providers
analysis = cohere_client.chat.completions.create(
    messages=[{"role": "user", "content": "Analyze renewable energy trends"}],
    response_model=TechAnalysis,
    temperature=0  # Cohere supports temperature parameter
)
```

#### 2. Direct GenAI Client Integration

```python
import instructor
from google import genai

# Create base client
base_client = genai.Client()

# Wrap with Instructor
client = instructor.from_genai(base_client)

# Use with structured outputs
result = client.chat.completions.create(
    messages=[{"role": "user", "content": "Extract key information about renewable energy"}],
    response_model=TechAnalysis
)
```

#### 3. Async Instructor Usage

```python
import asyncio
import instructor
from pydantic import BaseModel

class CodeReview(BaseModel):
    issues_found: List[str]
    suggestions: List[str]
    overall_quality: str
    maintainability_score: float

async def async_code_review():
    client = instructor.from_provider("google/gemini-2.5-flash")
    
    review = await client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": "Review this Python code: def add(a, b): return a + b"
        }],
        response_model=CodeReview
    )
    
    return review

# Run async review
review = asyncio.run(async_code_review())
```

#### 4. Multimodal with Instructor

```python
import instructor
from pydantic import BaseModel
from typing import List

class ImageAnalysis(BaseModel):
    objects_detected: List[str]
    scene_description: str
    colors_present: List[str]
    estimated_setting: str

client = instructor.from_provider("google/gemini-2.5-flash")

# Note: Instructor supports autodetect_images for automatic image handling
analysis = client.chat.completions.create(
    messages=[{
        "role": "user",
        "content": "Analyze this image: https://example.com/image.jpg"
    }],
    response_model=ImageAnalysis
)
```

### Performance Optimizations

#### 1. Connection Pooling

```python
from google import genai
from google.genai.types import HttpOptions
import aiohttp

# Configure HTTP options for better performance
http_options = HttpOptions(
    async_client_args={
        'connector': aiohttp.TCPConnector(limit=100),
        'timeout': aiohttp.ClientTimeout(total=30)
    }
)

client = genai.Client(http_options=http_options)
```

#### 2. Caching Strategies

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=128)
def get_cached_response(prompt_hash: str, model: str):
    """Cache responses for identical prompts."""
    # Implementation would store/retrieve from cache
    pass

async def generate_with_cache(prompt: str, model: str = 'gemini-2.5-flash'):
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    
    # Check cache first
    cached = get_cached_response(prompt_hash, model)
    if cached:
        return cached
    
    # Generate new response
    client = genai.Client()
    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt
    )
    
    # Cache result
    get_cached_response.cache_info()
    return response
```

#### 3. Batch Processing

```python
import asyncio
from typing import List

async def batch_generate(prompts: List[str], model: str = 'gemini-2.5-flash'):
    """Process multiple prompts concurrently."""
    client = genai.Client()
    
    async def process_single(prompt: str):
        return await client.aio.models.generate_content(
            model=model,
            contents=prompt
        )
    
    # Process all prompts concurrently
    tasks = [process_single(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

# Usage
prompts = [
    "Explain machine learning",
    "What is quantum computing?", 
    "Describe blockchain technology"
]
results = asyncio.run(batch_generate(prompts))
```

</details>

## ⚠️ Important Considerations

<warnings>
- **EOL Deadline**: Legacy google-generativeai package support ends August 31, 2025
- **Streaming Limitations**: As of July 2025, no streaming support with structured outputs or function calling
- **Rate Limits**: New SDK may have different rate limiting behavior - test thoroughly
- **Breaking Changes**: Method signatures and response formats differ from legacy SDK
- **Authentication**: API key detection is automatic but verify environment variable names
- **Model Names**: Some model names have changed (e.g., gemini-1.5-pro vs gemini-2.5-flash)
- **Error Handling**: New error types and status codes require updated exception handling
- **Async Patterns**: Use client.aio for all async operations, not separate async clients
</warnings>

## 🔗 Resources

<references>
- [Google GenAI SDK Documentation](https://googleapis.github.io/python-genai/) - Official API reference
- [Migration Guide](https://ai.google.dev/gemini-api/docs/migrate) - Step-by-step migration instructions
- [Instructor GenAI Integration](https://python.useinstructor.com/integrations/genai/) - Structured outputs guide
- [GitHub Repository](https://github.com/googleapis/python-genai) - Source code and examples
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs) - General Gemini API guide
- [Vertex AI Integration](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview) - Enterprise usage patterns
</references>

## 🔗 Embedding Integration Patterns

### Cohere Embed v4 Integration

#### Modern Embedding API (v2)

```python
import cohere

# Initialize Cohere client
co = cohere.ClientV2()

# Text and image embedding
text_inputs = [
    {
        "content": [
            {"type": "text", "text": "Machine learning fundamentals"},
            {"type": "text", "text": "Neural network architecture"}
        ]
    },
]

response = co.embed(
    inputs=text_inputs,
    model="embed-v4.0",
    input_type="classification",  # or "search_document", "search_query"
    embedding_types=["float"]
)

# Access embeddings
embeddings = response.embeddings
print(f"Generated {len(embeddings)} embeddings")
```

#### Multimodal Embedding Support

```python
# Mixed content embedding (text + images)
multimodal_inputs = [
    {
        "content": [
            {"type": "text", "text": "Product description"},
            {"type": "image", "image": {"url": "https://example.com/product.jpg"}}
        ]
    }
]

response = co.embed(
    inputs=multimodal_inputs,
    model="embed-v4.0",
    input_type="search_document",
    embedding_types=["float"]
)
```

#### FastAPI Integration Example

```python
from fastapi import FastAPI
import cohere
from pydantic import BaseModel
from typing import List

app = FastAPI()
co = cohere.ClientV2()

class EmbeddingRequest(BaseModel):
    texts: List[str]
    input_type: str = "classification"

@app.post("/embed")
async def create_embeddings(request: EmbeddingRequest):
    """Create embeddings using Cohere Embed v4."""
    
    text_inputs = [
        {"content": [{"type": "text", "text": text}]}
        for text in request.texts
    ]
    
    response = co.embed(
        inputs=text_inputs,
        model="embed-v4.0",
        input_type=request.input_type,
        embedding_types=["float"]
    )
    
    return {
        "embeddings": response.embeddings,
        "model": "embed-v4.0",
        "dimensions": len(response.embeddings[0]) if response.embeddings else 0
    }
```

### Google GenAI Embedding Integration

```python
from google import genai

client = genai.Client()

# Text embedding (when available)
response = client.models.embed_content(
    model='text-embedding-004',
    contents=['Machine learning is transforming industries'],
    config={'output_dimensionality': 768}
)

print(f"Embedding dimensions: {len(response.values)}")
```

### Verba Integration Pattern

```python
# Example integration for Verba's embedding component
from goldenverba.components.interfaces import Embedding

class CohereEmbedder(Embedding):
    """Modern Cohere Embed v4 integration for Verba."""
    
    def __init__(self):
        super().__init__()
        self.name = "CohereEmbedV4"
        self.description = "Cohere Embed v4 with multimodal support"
        self.requires_library = ["cohere"]
        self.requires_env = ["CO_API_KEY"]
        
        # Configuration
        self.config["Model"] = {
            "type": "dropdown",
            "value": "embed-v4.0",
            "values": ["embed-v4.0"],
            "description": "Cohere embedding model"
        }
        
        self.config["Input Type"] = {
            "type": "dropdown", 
            "value": "search_document",
            "values": ["search_document", "search_query", "classification"],
            "description": "Type of input for optimal embedding"
        }
    
    async def aembed(self, config: dict, texts: List[str]) -> List[List[float]]:
        """Create embeddings asynchronously."""
        import cohere
        
        co = cohere.ClientV2()
        
        text_inputs = [
            {"content": [{"type": "text", "text": text}]}
            for text in texts
        ]
        
        response = co.embed(
            inputs=text_inputs,
            model=config.get("Model", {}).get("value", "embed-v4.0"),
            input_type=config.get("Input Type", {}).get("value", "search_document"),
            embedding_types=["float"]
        )
        
        return response.embeddings
```

## 📁 Migration Examples

### Legacy to New SDK Migration

#### Before (Legacy google-generativeai)

```python
import google.generativeai as genai

genai.configure(api_key="your-api-key")
model = genai.GenerativeModel('gemini-1.5-pro')
response = model.generate_content('Hello world')
print(response.text)

# Async (legacy)
import asyncio
async def generate():
    response = await model.generate_content_async('Hello world')
    return response.text
```

#### After (New google-genai SDK)

```python
from google import genai

# Client auto-detects GOOGLE_API_KEY or GEMINI_API_KEY
client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Hello world'
)
print(response.text)

# Async (new)
async def generate():
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash', 
        contents='Hello world'
    )
    return response.text
```

### FastAPI Integration Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
import instructor
import asyncio
from typing import List

app = FastAPI()

# Initialize clients
genai_client = genai.Client()
instructor_client = instructor.from_genai(genai_client)

class QueryRequest(BaseModel):
    prompt: str
    model: str = "gemini-2.5-flash"
    structured: bool = False

class StructuredResponse(BaseModel):
    answer: str
    confidence: float
    key_points: List[str]

@app.post("/generate")
async def generate_content(request: QueryRequest):
    """Generate content with optional structured output."""
    try:
        if request.structured:
            # Use Instructor for structured output
            response = await instructor_client.chat.completions.create(
                messages=[{"role": "user", "content": request.prompt}],
                response_model=StructuredResponse
            )
            return response
        else:
            # Use standard generation
            response = await genai_client.aio.models.generate_content(
                model=request.model,
                contents=request.prompt
            )
            return {"text": response.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-generate")
async def batch_generate(prompts: List[str]):
    """Process multiple prompts concurrently."""
    async def process_prompt(prompt: str):
        return await genai_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
    
    tasks = [process_prompt(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "results": [
            {"text": r.text} if hasattr(r, 'text') else {"error": str(r)}
            for r in results
        ]
    }
```

## 🏷️ Metadata

<meta>
research-date: 2025-08-05
confidence: high
version-checked: google-genai v1.0.0+, instructor v1.4.0+
migration-urgency: critical
eol-deadline: 2025-08-31
</meta>

---

## Implementation Checklist for Verba Migration

- [ ] Update dependencies: `pip install google-genai "instructor[google-genai]"`
- [ ] Replace legacy imports: `google.generativeai` → `google.genai`
- [ ] Update client initialization patterns
- [ ] Migrate async operations to `client.aio` methods
- [ ] Update environment variable names if needed
- [ ] Test structured output capabilities with existing schemas
- [ ] Verify streaming behavior and limitations
- [ ] Update error handling for new exception types
- [ ] Performance test with concurrent operations
- [ ] Update documentation and examples
