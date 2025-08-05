# LiteLLMGenerator.py
import os
from dotenv import load_dotenv
from goldenverba.components.interfaces import Generator
from goldenverba.components.types import InputConfig
from goldenverba.components.util import get_environment
import asyncio
from litellm import acompletion
import logging

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class LiteLLMGenerator(Generator):
    """
    LiteLLM Generator using unified API for 100+ LLM providers.
    """

    def __init__(self):
        super().__init__()
        self.name = "LiteLLM"
        self.description = "Using LiteLLM unified API to access 100+ LLM providers with OpenAI-compatible interface"
        self.context_window = 128000  # Default context window, model-specific

        # Popular models across different providers
        models = [
            # OpenAI Models
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
            
            # Anthropic Models
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            
            # Google Models
            "gemini/gemini-pro",
            "gemini/gemini-pro-vision",
            "vertex_ai/gemini-pro",
            
            # Azure OpenAI (requires deployment name)
            "azure/gpt-4o",
            "azure/gpt-35-turbo",
            
            # Cohere Models
            "cohere/command-r-plus",
            "cohere/command-r",
            "cohere/command",
            
            # Open Source Models
            "ollama/llama3.2",
            "ollama/llama3.1",
            "ollama/codellama",
            "ollama/mistral",
            
            # Together AI
            "together_ai/meta-llama/Llama-3-8b-chat-hf",
            "together_ai/meta-llama/Llama-3-70b-chat-hf",
            
            # HuggingFace
            "huggingface/microsoft/DialoGPT-medium",
            "huggingface/microsoft/DialoGPT-large",
            
            # Groq
            "groq/llama3-8b-8192",
            "groq/llama3-70b-8192",
            "groq/mixtral-8x7b-32768",
        ]

        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[0],
            description="Select a model from any supported LLM provider",
            values=models,
        )

        # API Keys for different providers
        self.config["OpenAI API Key"] = InputConfig(
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            description="OpenAI API Key (for OpenAI models)",
            values=[],
        )

        self.config["Anthropic API Key"] = InputConfig(
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            description="Anthropic API Key (for Claude models)",
            values=[],
        )

        self.config["Google API Key"] = InputConfig(
            type="password",
            value=os.getenv("GOOGLE_API_KEY", ""),
            description="Google API Key (for Gemini models)",
            values=[],
        )

        self.config["Cohere API Key"] = InputConfig(
            type="password",
            value=os.getenv("COHERE_API_KEY", ""),
            description="Cohere API Key (for Command models)",
            values=[],
        )

        self.config["HuggingFace API Key"] = InputConfig(
            type="password",
            value=os.getenv("HUGGINGFACE_API_KEY", ""),
            description="HuggingFace API Key (for HF models)",
            values=[],
        )

        self.config["Together API Key"] = InputConfig(
            type="password",
            value=os.getenv("TOGETHER_API_KEY", ""),
            description="Together AI API Key (for Together models)",
            values=[],
        )

        self.config["Groq API Key"] = InputConfig(
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            description="Groq API Key (for Groq models)",
            values=[],
        )

        # Azure specific settings
        self.config["Azure Base URL"] = InputConfig(
            type="text",
            value=os.getenv("AZURE_API_BASE", ""),
            description="Azure OpenAI Base URL (for Azure models)",
            values=[],
        )

        self.config["Azure API Version"] = InputConfig(
            type="text",
            value=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
            description="Azure OpenAI API Version",
            values=[],
        )

        # Ollama specific settings
        self.config["Ollama Base URL"] = InputConfig(
            type="text",
            value=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
            description="Ollama Base URL (for local Ollama models)",
            values=[],
        )

        # Model parameters
        self.config["Temperature"] = InputConfig(
            type="text",
            value="0.7",
            description="Temperature for response generation (0.0-2.0)",
            values=[],
        )

        self.config["Max Tokens"] = InputConfig(
            type="number",
            value=4096,
            description="Maximum tokens in response",
            values=[],
        )

        self.config["Top P"] = InputConfig(
            type="text",
            value="1.0",
            description="Top P sampling parameter (0.0-1.0)",
            values=[],
        )

        # Advanced features
        self.config["Enable Streaming"] = InputConfig(
            type="bool",
            value=True,
            description="Enable streaming responses",
            values=[],
        )

        self.config["Include Usage Stats"] = InputConfig(
            type="bool",
            value=True,
            description="Include token usage statistics",
            values=[],
        )

    def setup_environment_variables(self, config):
        """Set up environment variables for different providers based on config."""
        # Set API keys as environment variables for LiteLLM
        api_keys = {
            "OPENAI_API_KEY": config.get("OpenAI API Key", {}).get("value", ""),
            "ANTHROPIC_API_KEY": config.get("Anthropic API Key", {}).get("value", ""),
            "GOOGLE_API_KEY": config.get("Google API Key", {}).get("value", ""),
            "COHERE_API_KEY": config.get("Cohere API Key", {}).get("value", ""),
            "HUGGINGFACE_API_KEY": config.get("HuggingFace API Key", {}).get("value", ""),
            "TOGETHER_API_KEY": config.get("Together API Key", {}).get("value", ""),
            "GROQ_API_KEY": config.get("Groq API Key", {}).get("value", ""),
            "AZURE_API_BASE": config.get("Azure Base URL", {}).get("value", ""),
            "AZURE_API_VERSION": config.get("Azure API Version", {}).get("value", ""),
            "OLLAMA_API_BASE": config.get("Ollama Base URL", {}).get("value", ""),
        }

        for key, value in api_keys.items():
            if value:
                os.environ[key] = value

    async def generate_stream(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ):
        """Generate streaming response using LiteLLM."""
        
        # Set up environment variables
        self.setup_environment_variables(config)
        
        system_message = config.get("System Message").value
        model = config.get("Model", {"value": "gpt-4o-mini"}).value
        temperature = float(config.get("Temperature", {"value": "0.7"}).value)
        max_tokens = config.get("Max Tokens", {"value": 4096}).value
        top_p = float(config.get("Top P", {"value": "1.0"}).value)
        enable_streaming = config.get("Enable Streaming", {"value": True}).value
        include_usage = config.get("Include Usage Stats", {"value": True}).value

        messages = self.prepare_messages(query, context, conversation, system_message)

        try:
            logger.info(f"Generating response with LiteLLM model: {model}")
            
            # Prepare completion parameters
            completion_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
            }
            
            if enable_streaming:
                completion_params["stream"] = True
                if include_usage:
                    completion_params["stream_options"] = {"include_usage": True}
                
                # Stream response
                response_stream = await acompletion(**completion_params)
                
                run_id = "litellm_stream"
                
                async for chunk in response_stream:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        delta = chunk.choices[0].delta
                        
                        if hasattr(delta, 'content') and delta.content:
                            yield {
                                "message": delta.content,
                                "finish_reason": None,
                                "runId": run_id,
                                "type": "content"
                            }
                        
                        if hasattr(chunk.choices[0], 'finish_reason') and chunk.choices[0].finish_reason:
                            # Include usage statistics if available
                            usage_info = {}
                            if hasattr(chunk, 'usage') and chunk.usage:
                                usage_info = {
                                    "prompt_tokens": chunk.usage.prompt_tokens,
                                    "completion_tokens": chunk.usage.completion_tokens,
                                    "total_tokens": chunk.usage.total_tokens
                                }
                            
                            yield {
                                "message": "",
                                "finish_reason": chunk.choices[0].finish_reason,
                                "runId": run_id,
                                "usage": usage_info
                            }
                    
                    if hasattr(chunk, 'id'):
                        run_id = chunk.id
            else:
                # Non-streaming response
                response = await acompletion(**completion_params)
                
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                run_id = response.id if hasattr(response, 'id') else "litellm_complete"
                
                usage_info = {}
                if hasattr(response, 'usage') and response.usage:
                    usage_info = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                
                yield {
                    "message": content,
                    "finish_reason": finish_reason,
                    "runId": run_id,
                    "usage": usage_info
                }
                
        except Exception as e:
            logger.error(f"Error generating response with LiteLLM: {str(e)}")
            yield {
                "message": f"Error: {str(e)}",
                "finish_reason": "error",
                "runId": "error"
            }

    def prepare_messages(
        self, query: str, context: str, conversation: list[dict], system_message: str
    ) -> list[dict]:
        """Prepare messages in OpenAI format for LiteLLM."""
        messages = [
            {
                "role": "system",
                "content": system_message,
            }
        ]

        # Add conversation history
        for message in conversation:
            messages.append({"role": message.type, "content": message.content})

        # Add current query with context
        messages.append(
            {
                "role": "user",
                "content": f"Answer this query: '{query}' with this provided context: {context}",
            }
        )

        return messages

    def get_supported_providers(self) -> dict:
        """Return information about supported providers."""
        return {
            "openai": {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini"],
                "env_key": "OPENAI_API_KEY"
            },
            "anthropic": {
                "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
                "env_key": "ANTHROPIC_API_KEY"
            },
            "google": {
                "models": ["gemini/gemini-pro", "gemini/gemini-pro-vision", "vertex_ai/gemini-pro"],
                "env_key": "GOOGLE_API_KEY"
            },
            "cohere": {
                "models": ["cohere/command-r-plus", "cohere/command-r", "cohere/command"],
                "env_key": "COHERE_API_KEY"
            },
            "ollama": {
                "models": ["ollama/llama3.2", "ollama/llama3.1", "ollama/codellama", "ollama/mistral"],
                "env_key": "OLLAMA_API_BASE"
            },
            "azure": {
                "models": ["azure/gpt-4o", "azure/gpt-35-turbo"],
                "env_keys": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]
            },
            "groq": {
                "models": ["groq/llama3-8b-8192", "groq/llama3-70b-8192", "groq/mixtral-8x7b-32768"],
                "env_key": "GROQ_API_KEY"
            },
            "together_ai": {
                "models": ["together_ai/meta-llama/Llama-3-8b-chat-hf", "together_ai/meta-llama/Llama-3-70b-chat-hf"],
                "env_key": "TOGETHER_API_KEY"
            },
            "huggingface": {
                "models": ["huggingface/microsoft/DialoGPT-medium", "huggingface/microsoft/DialoGPT-large"],
                "env_key": "HUGGINGFACE_API_KEY"
            }
        }