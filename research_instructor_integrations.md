# Instructor Integrations Research Summary

_Generated: 2025-08-05 | Sources: 4_

## 🎯 Quick Reference

<key-points>
- Unified `from_provider()` initialization across all providers
- Pydantic BaseModel schemas for type-safe structured outputs
- Consistent async/sync patterns with streaming support
- Provider-specific modes for optimal performance
- Migration from legacy clients to modern Instructor patterns
</key-points>

## 📋 Overview

<summary>
Instructor provides a unified interface for structured data extraction across multiple LLM providers (OpenAI, Anthropic, Google, LiteLLM). It leverages Pydantic models for type validation and offers consistent patterns for async operations, streaming, and error handling.
</summary>

## 🔧 Implementation Details

<details>

### OpenAI Responses API Integration

The new Responses API provides a streamlined approach with built-in tools and simplified methods.

#### Basic Setup
```python
import instructor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# Initialize client
client = instructor.from_provider(
    "openai/gpt-4.1-mini", 
    mode=instructor.Mode.RESPONSES_TOOLS
)

# Create structured output
profile = client.responses.create(
    input="Extract out Ivan is 28 years old",
    response_model=User,
)
```

#### Async Implementation
```python
import asyncio

async def extract_async():
    client = instructor.from_provider(
        "openai/gpt-4.1-mini",
        mode=instructor.Mode.RESPONSES_TOOLS,
        async_client=True
    )
    
    profile = await client.responses.create(
        input="Extract: Jason is 25 years old",
        response_model=User,
    )
    return profile

user = asyncio.run(extract_async())
```

#### Streaming Support
```python
# Partial streaming for single objects
resp = client.responses.create_partial(
    input="Generate a fake profile",
    response_model=User,
)

for user in resp:
    print(user)  # Shows partial updates

# Iterable streaming for multiple objects
from typing import Iterable

profiles = client.responses.create(
    input="Generate three fake profiles",
    response_model=Iterable[User],
)

for profile in profiles:
    print(profile)
```

#### Built-in Tools
```python
class Citation(BaseModel):
    id: int
    url: str

class Summary(BaseModel):
    citations: list[Citation]
    summary: str

client = instructor.from_provider(
    "openai/gpt-4.1-mini",
    mode=instructor.Mode.RESPONSES_TOOLS_WITH_INBUILT_TOOLS,
)

# Web search tool
response = client.responses.create(
    input="What are the best restaurants around Granary Square?",
    tools=[{
        "type": "web_search_preview",
        "user_location": {
            "type": "approximate",
            "country": "GB",
            "city": "London",
            "region": "London",
        }
    }],
    response_model=Summary,
)

# File search tool
response = client.responses.create(
    input="How much does the Kyoto itinerary cost?",
    tools=[{
        "type": "file_search",
        "vector_store_ids": ["your_vector_store_id"],
        "max_num_results": 2,
    }],
    response_model=Response,
)
```

### Anthropic Integration

Anthropic offers robust support with multiple modes and advanced features like multimodal processing and thinking capabilities.

#### Basic Setup
```python
import instructor
from pydantic import BaseModel, Field
from typing import List

class Properties(BaseModel):
    name: str = Field(description="The name of the property")
    value: str = Field(description="The value of the property")

class User(BaseModel):
    name: str = Field(description="The user's full name")
    age: int = Field(description="The user's age in years")
    properties: List[Properties] = Field(description="List of user properties")

client = instructor.from_provider(
    "anthropic/claude-3-haiku-20240307",
    mode=instructor.Mode.ANTHROPIC_TOOLS
)

user_response = client.chat.completions.create(
    max_tokens=1024,
    messages=[
        {
            "role": "system",
            "content": "Extract structured information based on the user's request."
        },
        {
            "role": "user",
            "content": "Create a user for a model with a name, age, and properties.",
        }
    ],
    response_model=User,
)
```

#### Parallel Tool Calling
```python
from typing import Iterable, Literal

class Weather(BaseModel):
    location: str
    units: Literal["imperial", "metric"]

class GoogleSearch(BaseModel):
    query: str

client = instructor.from_provider(
    "anthropic/claude-3-haiku-20240307",
    mode=instructor.Mode.ANTHROPIC_PARALLEL_TOOLS,
)

results = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You must always use tools"},
        {
            "role": "user",
            "content": "What is the weather in toronto and dallas and who won the super bowl?",
        },
    ],
    response_model=Iterable[Weather | GoogleSearch],
)
```

#### Multimodal Support
```python
from instructor.multimodal import Image, PDF

class ImageDescription(BaseModel):
    objects: list[str] = Field(..., description="The objects in the image")
    scene: str = Field(..., description="The scene of the image")
    colors: list[str] = Field(..., description="The colors in the image")

# Image processing
response = client.chat.completions.create(
    response_model=ImageDescription,
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": [
                "What is in this image?",
                Image.from_url("https://example.com/image.jpg"),
                # Alternative methods:
                # Image.from_path("path/to/local/image.jpg")
                # Image.from_base64("base64_encoded_string_here")
            ],
        },
    ],
)

# PDF processing with caching
from instructor.multimodal import PdfWithCacheControl

class Receipt(BaseModel):
    total: int
    items: list[str]

response, completion = client.chat.completions.create_with_completion(
    response_model=Receipt,
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": [
                "Extract out the total and line items from the invoice",
                PdfWithCacheControl.from_url("https://example.com/invoice.pdf"),
            ],
        },
    ],
)
```

#### Streaming Patterns
```python
# Partial streaming
for partial_user in client.chat.completions.create_partial(
    messages=[
        {"role": "system", "content": "Create a detailed user profile"},
        {"role": "user", "content": "Create a user profile for Jason, age 25"},
    ],
    response_model=User,
    max_tokens=4096,
):
    print(f"Current state: {partial_user}")

# Iterable streaming
users = client.chat.completions.create_iterable(
    messages=[
        {
            "role": "user",
            "content": """
            Extract users:
            1. Jason is 25 years old
            2. Sarah is 30 years old
            3. Mike is 28 years old
            """,
        },
    ],
    response_model=User,
)

for user in users:
    print(user)
```

#### Thinking Support (Claude 3.7)
```python
class Answer(BaseModel):
    answer: float

client = instructor.from_provider("anthropic/claude-3-sonnet-20241022")
response = client.chat.completions.create(
    response_model=Answer,
    messages=[
        {
            "role": "user",
            "content": "Which is larger, 9.11 or 9.8",
        },
    ],
    temperature=1,
    max_tokens=2000,
    thinking={"type": "enabled", "budget_tokens": 1024},
)
```

### Google/Gemini Integration

Google's integration uses the new GenAI SDK with strong multimodal capabilities.

#### Basic Setup
```python
import instructor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# Using from_provider (recommended)
client = instructor.from_provider(
    "google/gemini-1.5-flash-latest",
)

resp = client.messages.create(
    messages=[
        {
            "role": "user",
            "content": "Extract Jason is 25 years old.",
        }
    ],
    response_model=User,
)
```

#### Configuration Options
```python
client = instructor.from_provider(
    "google/gemini-1.5-flash-latest",
    mode=instructor.Mode.GEMINI_JSON,
)

resp = client.messages.create(
    messages=[
        {
            "role": "user",
            "content": "Extract Jason is 25 years old.",
        },
    ],
    response_model=User,
    generation_config={
        "temperature": 0.5,
        "max_tokens": 1000,
        "top_p": 1,
        "top_k": 32,
    },
)
```

#### Nested Models
```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class User(BaseModel):
    name: str
    age: int
    addresses: list[Address]

user = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": """
            Extract: Jason is 25 years old.
            He lives at 123 Main St, New York, USA
            and has a summer house at 456 Beach Rd, Miami, USA
            """,
        },
    ],
    response_model=User,
)
```

#### Migration from Legacy SDK
```python
# Old Way (Deprecated)
import google.generativeai as genai
client = instructor.from_gemini(
    genai.GenerativeModel("gemini-1.5-flash"),
    mode=instructor.Mode.GEMINI_JSON,
)

# New Way (Recommended)
client = instructor.from_provider("google/gemini-1.5-flash")

# For Vertex AI
client = instructor.from_provider(
    "vertexai/gemini-1.5-flash",
    project="your-project",
    location="us-central1"
)
```

### LiteLLM Integration

LiteLLM provides a unified interface across multiple providers with built-in cost tracking.

#### Basic Setup
```python
import instructor
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

client = instructor.from_provider("litellm/gpt-3.5-turbo")

user = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Extract: Jason is 25 years old"},
    ],
    response_model=User,
)
```

#### Cost Calculation
```python
instructor_resp, raw_completion = client.chat.completions.create_with_completion(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Extract Jason is 25 years old.",
        }
    ],
    response_model=User,
)

print(raw_completion._hidden_params["response_cost"])
# Output: 0.00189
```

</details>

## ⚠️ Important Considerations

<warnings>
- Always use `from_provider()` for modern initialization patterns
- Avoid validators in response models when streaming to prevent breaking the stream
- Provider-specific features may have different availability and limitations
- Error handling patterns should account for validation failures and provider-specific errors
- Migration from legacy SDKs requires updating initialization and mode selection
</warnings>

## 🔗 Resources

<references>
- [OpenAI Responses API](https://python.useinstructor.com/integrations/openai-responses/) - New streamlined API with built-in tools
- [Anthropic Integration](https://python.useinstructor.com/integrations/anthropic/) - Multimodal and thinking capabilities
- [Google Integration](https://python.useinstructor.com/integrations/google/) - GenAI SDK migration guide
- [LiteLLM Integration](https://python.useinstructor.com/integrations/litellm/) - Unified provider interface
</references>

## 🏷️ Metadata

<meta>
research-date: 2025-08-05
confidence: high
version-checked: instructor>=1.0.0
providers-covered: openai, anthropic, google, litellm
</meta>