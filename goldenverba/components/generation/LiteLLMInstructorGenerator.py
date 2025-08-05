# LiteLLMInstructorGenerator.py - Enhanced LiteLLM generator with Instructor integration
import os
from dotenv import load_dotenv
from goldenverba.components.interfaces import Generator
from goldenverba.components.types import InputConfig
from goldenverba.components.util import get_environment
from goldenverba.components.schemas import (
    RAGResponse, EnhancedRAGResponse, Citation, ReasoningStep, ThinkingTrace,
    ConfidenceLevel, SourceType, create_citation_from_chunk
)
import asyncio
import instructor
from instructor.mode import Mode
from pydantic import BaseModel, Field
import logging
import time
from typing import List, Optional, Dict, Any, AsyncIterator

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class LiteLLMInstructorGenerator(Generator):
    """
    Enhanced LiteLLM Generator using Instructor for structured outputs.
    Supports 100+ LLM providers with unified interface and cost tracking.
    """

    def __init__(self):
        super().__init__()
        self.name = "LiteLLM Instructor"
        self.description = "Enhanced LiteLLM generator with structured outputs supporting 100+ LLM providers"
        self.context_window = 128000  # Default, model-specific

        # Popular models across different providers (updated August 2025)
        models = [
            # OpenAI Models
            "openai/o3",                    # Latest reasoning model
            "openai/o4-mini",               # Fast reasoning model
            "openai/gpt-4.1",               # Flagship model
            "openai/gpt-4.1-mini",          # Smaller variant
            "openai/gpt-4o-2025-08-01",     # Latest GPT-4o
            "openai/gpt-4o-mini",           # Cost-effective
            "openai/o1-preview",            # Previous reasoning
            "openai/o1-mini",               # Smaller o1
            
            # Anthropic Models
            "anthropic/claude-opus-4",      # Most powerful Claude
            "anthropic/claude-sonnet-4",    # Balanced Claude 4
            "anthropic/claude-3.7-sonnet",  # Coding-focused
            "anthropic/claude-3-7-sonnet-20250219",
            "anthropic/claude-3.5-sonnet-20241022",
            "anthropic/claude-3.5-haiku-20241022",
            
            # Google Models
            "gemini/gemini-1.5-flash",      # Fast Gemini
            "gemini/gemini-1.5-pro",        # Advanced Gemini
            "gemini/gemini-2.0-flash-exp",  # Experimental
            "vertex_ai/gemini-1.5-flash",   # Vertex AI
            "vertex_ai/gemini-1.5-pro",     # Vertex AI Pro
            
            # Azure OpenAI
            "azure/gpt-4o",
            "azure/gpt-4o-mini",
            "azure/gpt-35-turbo",
            
            # Cohere Models
            "cohere/command-r-plus-08-2024",
            "cohere/command-r-plus",
            "cohere/command-r",
            "cohere/command",
            
            # Open Source Models
            "ollama/llama3.2",
            "ollama/llama3.1:70b",
            "ollama/codellama:34b",
            "ollama/mistral:7b",
            "ollama/phi3:14b",
            
            # Together AI
            "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1",
            
            # Groq (Fast inference)
            "groq/llama-3.1-70b-versatile",
            "groq/llama-3.1-8b-instant",
            "groq/mixtral-8x7b-32768",
            "groq/gemma2-9b-it",
            
            # Perplexity
            "perplexity/llama-3.1-sonar-large-128k-online",
            "perplexity/llama-3.1-sonar-small-128k-online",
        ]

        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[4],  # Default to gpt-4o-2025-08-01 for reliability
            description="Select a model from any supported LLM provider",
            values=models,
        )

        # Provider-specific API Keys
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

        self.config["Groq API Key"] = InputConfig(
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            description="Groq API Key (for Groq models)",
            values=[],
        )

        self.config["Together API Key"] = InputConfig(
            type="password",
            value=os.getenv("TOGETHER_API_KEY", ""),
            description="Together AI API Key",
            values=[],
        )

        self.config["Perplexity API Key"] = InputConfig(
            type="password",
            value=os.getenv("PERPLEXITY_API_KEY", ""),
            description="Perplexity API Key",
            values=[],
        )

        # Azure specific settings
        self.config["Azure Base URL"] = InputConfig(
            type="text",
            value=os.getenv("AZURE_API_BASE", ""),
            description="Azure OpenAI Base URL",
            values=[],
        )

        self.config["Azure API Version"] = InputConfig(
            type="text",
            value=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
            description="Azure OpenAI API Version",
            values=[],
        )

        # Vertex AI settings
        self.config["Google Project ID"] = InputConfig(
            type="text",
            value=os.getenv("GOOGLE_PROJECT_ID", ""),
            description="Google Cloud Project ID (for Vertex AI)",
            values=[],
        )

        self.config["Google Region"] = InputConfig(
            type="text",
            value=os.getenv("GOOGLE_REGION", "us-central1"),
            description="Google Cloud Region (for Vertex AI)",
            values=[],
        )

        # Ollama settings
        self.config["Ollama Base URL"] = InputConfig(
            type="text",
            value=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
            description="Ollama Base URL (for local models)",
            values=[],
        )

        # Instructor configuration
        self.config["Use Structured Output"] = InputConfig(
            type="bool",
            value=True,
            description="Use structured Pydantic models for enhanced responses",
            values=[],
        )

        self.config["Response Format"] = InputConfig(
            type="dropdown",
            value="enhanced",
            description="Response format level",
            values=["basic", "standard", "enhanced"],
        )

        # Advanced features
        self.config["Enable Cost Tracking"] = InputConfig(
            type="bool",
            value=True,
            description="Track and display API costs",
            values=[],
        )

        self.config["Enable Reasoning Traces"] = InputConfig(
            type="bool",
            value=True,
            description="Show reasoning process for supported models",
            values=[],
        )

        self.config["Temperature"] = InputConfig(
            type="text",
            value="0.7",
            description="Control randomness (0.0-2.0)",
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

        # Initialize clients
        self.client = None
        self.instructor_client = None

    async def initialize_client(self, config):
        """Initialize LiteLLM instructor client."""
        try:
            # Set up environment variables for LiteLLM
            self.setup_environment_variables(config)
            
            model = config.get("Model", {"value": "openai/gpt-4o-mini"}).value
            
            # Initialize instructor client with LiteLLM provider
            self.instructor_client = instructor.from_provider(
                f"litellm/{model}",
                mode=Mode.TOOLS  # Use tools mode for maximum compatibility
            )
            
            logger.info(f"Initialized LiteLLM Instructor client for model: {model}")
            
        except Exception as e:
            logger.error(f"Error initializing LiteLLM Instructor client: {str(e)}")
            raise

    def setup_environment_variables(self, config):
        """Set up environment variables for different providers based on config."""
        api_keys = {
            "OPENAI_API_KEY": config.get("OpenAI API Key", {}).get("value", ""),
            "ANTHROPIC_API_KEY": config.get("Anthropic API Key", {}).get("value", ""),
            "GOOGLE_API_KEY": config.get("Google API Key", {}).get("value", ""),
            "COHERE_API_KEY": config.get("Cohere API Key", {}).get("value", ""),
            "GROQ_API_KEY": config.get("Groq API Key", {}).get("value", ""),
            "TOGETHER_API_KEY": config.get("Together API Key", {}).get("value", ""),
            "PERPLEXITY_API_KEY": config.get("Perplexity API Key", {}).get("value", ""),
            "AZURE_API_BASE": config.get("Azure Base URL", {}).get("value", ""),
            "AZURE_API_VERSION": config.get("Azure API Version", {}).get("value", ""),
            "GOOGLE_PROJECT_ID": config.get("Google Project ID", {}).get("value", ""),
            "GOOGLE_REGION": config.get("Google Region", {}).get("value", ""),
            "OLLAMA_API_BASE": config.get("Ollama Base URL", {}).get("value", ""),
        }

        for key, value in api_keys.items():
            if value:
                os.environ[key] = value

    async def generate_structured_response(
        self, 
        messages: List[Dict], 
        model: str, 
        config: Dict,
        response_format: str = "enhanced"
    ) -> EnhancedRAGResponse:
        """Generate a structured response using LiteLLM + Instructor."""
        
        logger.info(f"Generating structured response with LiteLLM model: {model}")
        start_time = time.time()

        # Check provider-specific capabilities
        provider = model.split("/")[0] if "/" in model else "unknown"
        supports_reasoning = any(model_type in model.lower() for model_type in ["o1", "o3", "o4", "claude"])
        enable_cost_tracking = config.get("Enable Cost Tracking", {}).get("value", True)

        try:
            # Select response model based on format
            if response_format == "enhanced":
                response_model = EnhancedRAGResponse
            else:
                response_model = RAGResponse

            # Prepare completion parameters
            completion_params = {
                "messages": messages,
                "response_model": response_model,
                "temperature": float(config.get("Temperature", {}).get("value", "0.7")),
                "max_tokens": config.get("Max Tokens", {}).get("value", 4096),
                "top_p": float(config.get("Top P", {}).get("value", "1.0")),
                "max_retries": 2
            }

            # Generate structured response
            if enable_cost_tracking:
                # Use create_with_completion to get cost information
                response, raw_completion = await self.instructor_client.chat.completions.create_with_completion(
                    **completion_params
                )
                
                # Extract cost information
                cost_info = {}
                if hasattr(raw_completion, '_hidden_params') and 'response_cost' in raw_completion._hidden_params:
                    cost_info = {
                        "cost": raw_completion._hidden_params['response_cost'],
                        "currency": "USD"
                    }
            else:
                response = await self.instructor_client.chat.completions.create(**completion_params)
                cost_info = {}

            # Add metadata
            generation_time = time.time() - start_time
            response.generation_time = generation_time
            response.model_name = model
            response.token_usage = cost_info

            # Add provider-specific enhancements
            if supports_reasoning:
                if not response.reasoning_trace:
                    response.reasoning_trace = ThinkingTrace(
                        reasoning_steps=[],
                        final_conclusion=response.answer,
                        complexity_level="automated"
                    )

            # Add provider information
            response.tools_used = [f"litellm_{provider}"]
            if hasattr(response, 'tool_results'):
                response.tool_results["provider"] = provider
                response.tool_results["cost_tracking"] = enable_cost_tracking

            logger.info(f"Structured response generated in {generation_time:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Error generating structured response: {str(e)}")
            # Return a basic error response
            return EnhancedRAGResponse(
                answer=f"I apologize, but I encountered an error while generating a response: {str(e)}",
                confidence_level=ConfidenceLevel.LOW,
                model_name=model,
                error_messages=[str(e)],
                generation_time=time.time() - start_time
            )

    async def generate_stream(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ):
        """Generate streaming response with structured output support."""
        
        if not self.instructor_client:
            await self.initialize_client(config)

        system_message = config.get("System Message").value
        model = config.get("Model", {"value": "openai/gpt-4o-mini"}).value
        use_structured = config.get("Use Structured Output", {"value": True}).value
        response_format = config.get("Response Format", {"value": "enhanced"}).value

        messages = self.prepare_messages(query, context, conversation, system_message)

        try:
            if use_structured:
                # Generate structured response
                structured_response = await self.generate_structured_response(
                    messages, model, config, response_format
                )
                
                # Stream the structured response
                yield from self.stream_structured_response(structured_response)
            else:
                # Fall back to regular LiteLLM streaming
                yield from await self.generate_regular_stream(messages, model, config)

        except Exception as e:
            logger.error(f"Error in generate_stream: {str(e)}")
            yield {
                "message": f"Error: {str(e)}",
                "finish_reason": "error",
                "runId": "error"
            }

    def stream_structured_response(self, response: EnhancedRAGResponse) -> AsyncIterator[dict]:
        """Stream a structured response in chunks with LiteLLM-specific formatting."""
        run_id = f"litellm_{int(time.time())}"
        
        # Stream provider information
        provider = response.model_name.split("/")[0] if "/" in response.model_name else "unknown"
        yield {
            "message": f"## 🔗 Provider: {provider.upper()}\n\n",
            "finish_reason": None,
            "runId": run_id,
            "type": "provider_header"
        }

        # Stream reasoning trace if available
        if response.reasoning_trace and response.reasoning_trace.reasoning_steps:
            yield {
                "message": "## 🧠 Reasoning Process\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "reasoning_header"
            }
            
            for step in response.reasoning_trace.reasoning_steps:
                yield {
                    "message": f"**Step {step.step_number}:** {step.description}\n{step.content}\n\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "reasoning_step"
                }

        # Stream main answer
        yield {
            "message": "## 💬 Response\n\n",
            "finish_reason": None,
            "runId": run_id,
            "type": "answer_header"
        }

        # Stream answer in natural chunks
        answer_sentences = response.answer.split('. ')
        for sentence in answer_sentences:
            if sentence.strip():
                yield {
                    "message": sentence + ('. ' if not sentence.endswith('.') else ' '),
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "content"
                }

        # Stream key insights
        if response.key_insights:
            yield {
                "message": "\n\n## 💡 Key Insights\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "insights_header"
            }
            
            for insight in response.key_insights:
                yield {
                    "message": f"• {insight}\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "insight"
                }

        # Stream citations
        if response.citations:
            yield {
                "message": "\n\n## 📖 Sources\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "citations_header"
            }
            
            for i, citation in enumerate(response.citations, 1):
                citation_text = f"[{i}] **{citation.title or 'Source'}**\n{citation.content_snippet}\n\n"
                yield {
                    "message": citation_text,
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "citation"
                }

        # Stream limitations if any
        if response.limitations:
            yield {
                "message": "\n\n## ⚠️ Limitations\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "limitations_header"
            }
            
            for limitation in response.limitations:
                yield {
                    "message": f"• {limitation}\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "limitation"
                }

        # Stream follow-up questions
        if response.follow_up_questions:
            yield {
                "message": "\n\n## 🤔 Follow-up Questions\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "followup_header"
            }
            
            for question in response.follow_up_questions:
                yield {
                    "message": f"• {question}\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "followup"
                }

        # Final metadata with cost information
        metadata = {
            "confidence": response.confidence_level.value,
            "model": response.model_name,
            "provider": provider,
            "generation_time": response.generation_time,
            "sources_used": len(response.citations),
            "tools_used": response.tools_used,
            "cost_info": response.token_usage,
            "litellm_features": {
                "provider": provider,
                "unified_api": True,
                "cost_tracking": bool(response.token_usage)
            }
        }

        yield {
            "message": "",
            "finish_reason": "stop",
            "runId": run_id,
            "metadata": metadata
        }

    async def generate_regular_stream(self, messages: List[Dict], model: str, config: Dict):
        """Fall back to regular LiteLLM streaming for non-structured output."""
        from litellm import acompletion
        
        temperature = float(config.get("Temperature", {}).get("value", "0.7"))
        max_tokens = config.get("Max Tokens", {}).get("value", 4096)
        top_p = float(config.get("Top P", {}).get("value", "1.0"))
        
        completion_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True,
            "stream_options": {"include_usage": True}
        }
        
        try:
            response_stream = await acompletion(**completion_params)
            run_id = "litellm_regular_stream"
            
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
                        # Include usage and cost info if available
                        usage_info = {}
                        if hasattr(chunk, 'usage') and chunk.usage:
                            usage_info = {
                                "prompt_tokens": chunk.usage.prompt_tokens,
                                "completion_tokens": chunk.usage.completion_tokens,
                                "total_tokens": chunk.usage.total_tokens
                            }
                        
                        # Add cost information if available
                        if hasattr(chunk, '_hidden_params') and 'response_cost' in chunk._hidden_params:
                            usage_info["cost"] = chunk._hidden_params['response_cost']
                        
                        yield {
                            "message": "",
                            "finish_reason": chunk.choices[0].finish_reason,
                            "runId": run_id,
                            "usage": usage_info
                        }
                
                if hasattr(chunk, 'id'):
                    run_id = chunk.id
                    
        except Exception as e:
            logger.error(f"Error in regular streaming: {str(e)}")
            yield {
                "message": f"Error: {str(e)}",
                "finish_reason": "error",
                "runId": "error"
            }

    def prepare_messages(
        self, query: str, context: str, conversation: list[dict], system_message: str
    ) -> list[dict]:
        """Prepare messages optimized for LiteLLM unified interface."""
        
        # Enhanced system message for LiteLLM with multi-provider context
        enhanced_system = f"""{system_message}

As a multi-provider AI assistant using LiteLLM's unified interface:
1. Provide accurate, well-reasoned responses
2. Cite sources from the provided context
3. Adapt communication style to the underlying model's strengths
4. Be transparent about limitations
5. Suggest relevant follow-up questions

Context length: {len(context)} characters"""

        messages = [
            {
                "role": "system",
                "content": enhanced_system,
            }
        ]

        # Add conversation history
        for message in conversation:
            messages.append({"role": message.type, "content": message.content})

        # Add current query with context
        user_content = f"""Please analyze and respond to this query using the provided context.

Query: {query}

Relevant Context:
{context}

Please provide a comprehensive response that demonstrates reasoning and cites relevant sources."""

        messages.append({
            "role": "user",
            "content": user_content
        })

        return messages

    def extract_citations_from_context(self, context: str, max_citations: int = 6) -> List[Citation]:
        """Extract citations from context with LiteLLM-optimized processing."""
        citations = []
        
        context_sections = context.split('\n\n')
        
        for i, section in enumerate(context_sections[:max_citations]):
            if len(section.strip()) > 80:
                # Extract title from first line or create one
                lines = section.split('\n')
                potential_title = lines[0] if lines else f"LiteLLM Context {i+1}"
                
                citation = Citation(
                    source_id=f"litellm_context_{i}",
                    source_type=SourceType.DOCUMENT,
                    title=potential_title[:100] + "..." if len(potential_title) > 100 else potential_title,
                    content_snippet=section[:250] + "..." if len(section) > 250 else section,
                    confidence_score=0.8,
                    metadata={
                        "section_number": i + 1,
                        "length": len(section),
                        "processed_by": "litellm",
                        "provider": "unified"
                    }
                )
                citations.append(citation)
        
        return citations

    def get_supported_providers(self) -> Dict[str, Any]:
        """Return comprehensive information about supported providers."""
        return {
            "openai": {
                "models": ["o3", "o4-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4o-2025-08-01", "gpt-4o-mini"],
                "features": ["reasoning", "structured_output", "function_calling"],
                "env_key": "OPENAI_API_KEY"
            },
            "anthropic": {
                "models": ["claude-opus-4", "claude-sonnet-4", "claude-3.7-sonnet"],
                "features": ["thinking", "multimodal", "tool_use"],
                "env_key": "ANTHROPIC_API_KEY"
            },
            "google": {
                "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
                "features": ["multimodal", "code_execution", "grounding"],
                "env_key": "GOOGLE_API_KEY"
            },
            "cohere": {
                "models": ["command-r-plus", "command-r", "command"],
                "features": ["rag_optimized", "multilingual"],
                "env_key": "COHERE_API_KEY"
            },
            "groq": {
                "models": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                "features": ["ultra_fast", "low_latency"],
                "env_key": "GROQ_API_KEY"
            },
            "together_ai": {
                "models": ["Meta-Llama-3.1-70B-Instruct-Turbo", "Mixtral-8x7B-Instruct-v0.1"],
                "features": ["open_source", "customizable"],
                "env_key": "TOGETHER_API_KEY"
            },
            "perplexity": {
                "models": ["llama-3.1-sonar-large-128k-online", "llama-3.1-sonar-small-128k-online"],
                "features": ["web_search", "real_time", "citations"],
                "env_key": "PERPLEXITY_API_KEY"
            },
            "ollama": {
                "models": ["llama3.2", "llama3.1:70b", "codellama:34b", "mistral:7b"],
                "features": ["local_deployment", "privacy", "customizable"],
                "env_key": "OLLAMA_API_BASE"
            }
        }