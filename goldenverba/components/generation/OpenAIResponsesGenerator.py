# OpenAIResponsesGenerator.py - Enhanced OpenAI generator using Responses API
import logging
import os
import time
from collections.abc import AsyncIterator

import instructor
from dotenv import load_dotenv
from instructor.mode import Mode
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from openai import AsyncOpenAI

from goldenverba.components.interfaces import Generator
from goldenverba.components.schemas import (
    Citation,
    ConfidenceLevel,
    EnhancedRAGResponse,
    RAGResponse,
    SourceType,
)
from goldenverba.components.types import InputConfig
from goldenverba.components.util import get_environment

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class OpenAIResponsesGenerator(Generator):
    """
    Enhanced OpenAI Generator using the new Responses API with structured outputs.
    Supports web search, file search, and advanced reasoning traces.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "OpenAI Responses"
        self.description = "Enhanced OpenAI generator using Responses API with structured outputs, web search, and advanced reasoning"
        self.context_window = 1000000  # 1M tokens for GPT-4.1 family

        # Updated models for August 2025 - Responses API compatible
        models = [
            "o3",  # Smartest model to date, can "think with images"
            "o4-mini",  # Fast, cost-efficient reasoning for math/coding/visual
            "gpt-4.1",  # Flagship GPT-4.1 model
            "gpt-4.1-mini",  # Smaller, faster GPT-4.1 variant
            "gpt-4.1-nano",  # Most cost-effective GPT-4.1 variant
            "o1-preview",  # Previous reasoning model
            "o1-mini",  # Smaller o1 variant
            "gpt-4o-2025-08-01",  # Latest GPT-4o
            "gpt-4o-mini",  # Cost-effective GPT-4o
        ]

        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[6],  # Default to gpt-4o for reliability
            description="Select an OpenAI Model (Responses API compatible)",
            values=models,
        )

        if os.getenv("OPENAI_API_KEY") is None:
            self.config["API Key"] = InputConfig(
                type="password",
                value="",
                description="OpenAI API Key (required for Responses API)",
                values=[],
            )

        if os.getenv("OPENAI_BASE_URL") is None:
            self.config["URL"] = InputConfig(
                type="text",
                value="https://api.openai.com/v1",
                description="OpenAI API Base URL",
                values=[],
            )

        # Responses API specific features
        self.config["Enable Web Search"] = InputConfig(
            type="bool",
            value=True,
            description="Enable built-in web search for up-to-date information",
            values=[],
        )

        self.config["Enable File Search"] = InputConfig(
            type="bool",
            value=True,
            description="Enable built-in file search for document-based queries",
            values=[],
        )

        self.config["Show Reasoning Traces"] = InputConfig(
            type="bool",
            value=True,
            description="Show step-by-step reasoning process (for o1/o3/o4 models)",
            values=[],
        )

        self.config["Enable Image Analysis"] = InputConfig(
            type="bool",
            value=False,
            description="Enable 'think with images' capability (o3/o4-mini only)",
            values=[],
        )

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

        # Initialize clients
        self.client = None
        self.instructor_client = None

    async def initialize_client(self, config):
        """Initialize both regular and instructor clients."""
        openai_key = get_environment(
            config, "API Key", "OPENAI_API_KEY", "No OpenAI API Key found"
        )
        openai_url = get_environment(
            config, "URL", "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )

        # Regular OpenAI client for Responses API
        self.client = AsyncOpenAI(api_key=openai_key, base_url=openai_url)

        # Instructor client for structured outputs
        self.instructor_client = instructor.from_openai(
            AsyncOpenAI(api_key=openai_key, base_url=openai_url),
            mode=Mode.RESPONSES_TOOLS,  # Use Responses API mode
        )

    @traceable
    async def generate_structured_response(
        self,
        messages: list[dict],
        model: str,
        config: dict,
        response_format: str = "enhanced",
    ) -> EnhancedRAGResponse:
        """Generate a structured response using the Responses API."""

        logger.info(f"Generating structured response with model: {model}")
        start_time = time.time()

        # Configure tools based on settings
        tools = []
        if config.get("Enable Web Search", {}).get("value", True):
            tools.append("web_search")
        if config.get("Enable File Search", {}).get("value", True):
            tools.append("file_search")

        # Check for reasoning model capabilities
        supports_image_thinking = model in ["o3", "o4-mini"]
        enable_images = config.get("Enable Image Analysis", {}).get("value", False)

        if supports_image_thinking and enable_images:
            tools.append("image_analysis")

        try:
            # Use the appropriate response model based on format
            if response_format == "enhanced":
                response_model = EnhancedRAGResponse
            else:
                response_model = RAGResponse

            # Generate structured response
            response = await self.instructor_client.responses.create(
                model=model,
                response_model=response_model,
                messages=messages,
                tools=tools,
                temperature=float(config.get("Temperature", {}).get("value", "0.7")),
                max_tokens=config.get("Max Tokens", {}).get("value", 4096),
                store=True,  # Enable state management
                max_retries=2,
            )

            # Add metadata
            generation_time = time.time() - start_time
            response.generation_time = generation_time
            response.model_name = model
            response.tools_used = tools

            # Get run information for tracing
            run = get_current_run_tree()
            if run:
                response.token_usage = {
                    "run_id": run.id,
                    "generation_time": generation_time,
                }

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
                generation_time=time.time() - start_time,
            )

    async def generate_stream(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ):
        """Generate streaming response with structured output support."""

        if not self.client or not self.instructor_client:
            await self.initialize_client(config)

        system_message = config.get("System Message").value
        model = config.get("Model", {"value": "gpt-4o-mini"}).value
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
                async for chunk in self.stream_structured_response(structured_response):
                    yield chunk
            else:
                # Fall back to regular streaming
                async for chunk in self.generate_regular_stream(
                    messages, model, config
                ):
                    yield chunk

        except Exception as e:
            logger.error(f"Error in generate_stream: {str(e)}")
            yield {
                "message": f"Error: {str(e)}",
                "finish_reason": "error",
                "runId": "error",
            }

    def stream_structured_response(
        self, response: EnhancedRAGResponse
    ) -> AsyncIterator[dict]:
        """Stream a structured response in chunks."""
        run_id = response.token_usage.get("run_id", "structured_response")

        # Stream reasoning trace if available
        if response.reasoning_trace and response.reasoning_trace.reasoning_steps:
            yield {
                "message": "## 🧠 Reasoning Process\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "reasoning_header",
            }

            for step in response.reasoning_trace.reasoning_steps:
                yield {
                    "message": f"**Step {step.step_number}:** {step.description}\n{step.content}\n\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "reasoning_step",
                }

        # Stream main answer
        yield {
            "message": "## 📝 Answer\n\n",
            "finish_reason": None,
            "runId": run_id,
            "type": "answer_header",
        }

        # Stream answer in chunks for better UX
        answer_chunks = [
            response.answer[i : i + 100] for i in range(0, len(response.answer), 100)
        ]
        for chunk in answer_chunks:
            yield {
                "message": chunk,
                "finish_reason": None,
                "runId": run_id,
                "type": "content",
            }

        # Stream citations if available
        if response.citations:
            yield {
                "message": "\n\n## 📚 Sources\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "citations_header",
            }

            for i, citation in enumerate(response.citations, 1):
                citation_text = f"{i}. **{citation.title or 'Source'}** - {citation.content_snippet}\n"
                yield {
                    "message": citation_text,
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "citation",
                }

        # Stream key insights if available
        if response.key_insights:
            yield {
                "message": "\n\n## 💡 Key Insights\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "insights_header",
            }

            for insight in response.key_insights:
                yield {
                    "message": f"• {insight}\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "insight",
                }

        # Stream follow-up questions if available
        if response.follow_up_questions:
            yield {
                "message": "\n\n## ❓ Follow-up Questions\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "followup_header",
            }

            for question in response.follow_up_questions:
                yield {
                    "message": f"• {question}\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "followup",
                }

        # Final metadata
        metadata = {
            "confidence": response.confidence_level.value,
            "model": response.model_name,
            "generation_time": response.generation_time,
            "sources_used": len(response.citations),
            "tools_used": response.tools_used,
        }

        yield {
            "message": "",
            "finish_reason": "stop",
            "runId": run_id,
            "metadata": metadata,
        }

    async def generate_regular_stream(
        self, messages: list[dict], model: str, config: dict
    ):
        """Fall back to regular streaming for non-structured output."""
        temperature = float(config.get("Temperature", {}).get("value", "0.7"))

        response_stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=temperature,
            max_tokens=config.get("Max Tokens", {}).get("value", 4096),
        )

        run_id = "regular_stream"

        async for chunk in response_stream:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta

                if hasattr(delta, "content") and delta.content:
                    yield {
                        "message": delta.content,
                        "finish_reason": None,
                        "runId": run_id,
                        "type": "content",
                    }

                if (
                    hasattr(chunk.choices[0], "finish_reason")
                    and chunk.choices[0].finish_reason
                ):
                    yield {
                        "message": "",
                        "finish_reason": chunk.choices[0].finish_reason,
                        "runId": run_id,
                    }

    def prepare_messages(
        self, query: str, context: str, conversation: list[dict], system_message: str
    ) -> list[dict]:
        """Prepare messages with enhanced context for Responses API."""

        # Enhanced system message for structured outputs
        enhanced_system = f"""{system_message}

When responding to queries, please:
1. Provide comprehensive, well-structured answers
2. Include relevant citations from the provided context
3. Show your reasoning process when appropriate
4. Suggest follow-up questions when relevant
5. Indicate your confidence level in the response
6. Highlight key insights and important limitations

Context provided: {len(context)} characters of relevant information."""

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
        messages.append(
            {
                "role": "user",
                "content": f"""Query: {query}

Relevant Context:
{context}

Please provide a comprehensive response using the context provided above.""",
            }
        )

        return messages

    def extract_citations_from_context(
        self, context: str, max_citations: int = 5
    ) -> list[Citation]:
        """Extract citations from the provided context."""
        citations = []

        # Simple extraction - in practice, this would be more sophisticated
        context_chunks = context.split("\n\n")[:max_citations]

        for i, chunk in enumerate(context_chunks):
            if len(chunk.strip()) > 50:  # Only meaningful chunks
                citation = Citation(
                    source_id=f"context_chunk_{i}",
                    source_type=SourceType.CHUNK,
                    title=f"Context Source {i + 1}",
                    content_snippet=chunk[:200] + "..." if len(chunk) > 200 else chunk,
                    confidence_score=0.8,
                )
                citations.append(citation)

        return citations
