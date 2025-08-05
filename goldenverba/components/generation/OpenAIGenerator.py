# OpenAIGenerator.py
import os
from dotenv import load_dotenv
from goldenverba.components.interfaces import Generator
from goldenverba.components.types import InputConfig
from goldenverba.components.util import get_environment
import asyncio
import instructor
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
import logging

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class AnswerResponse(BaseModel):
    """
    Model for the answer response with reasoning traces.
    """
    answer: str = Field(..., description="The generated answer to the query")
    reasoning: str = Field(..., description="The reasoning behind the answer")
    thinking_steps: list[str] = Field(default_factory=list, description="Step-by-step thinking process")
    confidence: float = Field(default=1.0, description="Confidence score for the answer")

class OpenAIGenerator(Generator):
    """
    OpenAI Generator using LangSmith and Instructor.
    """

    def __init__(self):
        super().__init__()
        self.name = "OpenAI"
        self.description = "Using OpenAI LLM models with LangSmith and Instructor to generate answers to queries"
        # Set context window based on model capabilities
        # GPT-4.1 models support 1M tokens, o4/o3 models support various context windows
        self.context_window = 1000000  # 1M tokens for GPT-4.1 family

        # Updated models for August 2025
        models = [
            "o3",                # Smartest model to date, can "think with images"
            "o4-mini",           # Fast, cost-efficient reasoning for math/coding/visual
            "gpt-4.1",           # Flagship GPT-4.1 model
            "gpt-4.1-mini",      # Smaller, faster GPT-4.1 variant
            "gpt-4.1-nano",      # Most cost-effective GPT-4.1 variant
            "o1-preview",        # Previous reasoning model
            "o1-mini",           # Smaller o1 variant
            "gpt-4o-2025-08-01", # Latest GPT-4o
            "gpt-4o-mini",       # Cost-effective GPT-4o
            # GPT-4.5 deprecated as of July 14, 2025
            # GPT-5 coming soon (early August 2025)
        ]

        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[0],
            description="Select an OpenAI Model",
            values=models,
        )

        if os.getenv("OPENAI_API_KEY") is None:
            self.config["API Key"] = InputConfig(
                type="password",
                value="",
                description="You can set your OpenAI API Key here or set it as environment variable `OPENAI_API_KEY`",
                values=[],
            )
        if os.getenv("OPENAI_BASE_URL") is None:
            self.config["URL"] = InputConfig(
                type="text",
                value="https://api.openai.com/v1",
                description="You can change the Base URL here if needed",
                values=[],
            )

        # Initialize OpenAI client
        self.client = None
        
        # Add configuration for Responses API features
        self.config["Enable Web Search"] = InputConfig(
            type="bool",
            value=False,
            description="Enable web search for more up-to-date information",
            values=[],
        )
        
        self.config["Enable File Search"] = InputConfig(
            type="bool",
            value=False,
            description="Enable file search for document-based queries",
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
        
        self.config["Temperature"] = InputConfig(
            type="text",
            value="0.7",
            description="Temperature for response generation (0.0-2.0)",
            values=[],
        )

    async def initialize_client(self, config):
        openai_key = get_environment(
            config, "API Key", "OPENAI_API_KEY", "No OpenAI API Key found"
        )
        openai_url = get_environment(
            config, "URL", "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )

        async_client = AsyncOpenAI(api_key=openai_key, base_url=openai_url)
        self.client = instructor.apatch(async_client)

    @traceable
    async def generate_answer(self, messages: list, model: str) -> tuple[AnswerResponse, str]:
        # Log the model being used for answer generation
        logger.info(f"Generating answer with model: {model}")

        # Create the responses API request
        # The responses API provides built-in tools and better state management
        response = await self.client.responses.create(
            model=model,
            response_model=AnswerResponse,
            max_retries=2,
            messages=messages,
            tools=[],  # Can add web_search, file_search, etc. if needed
            store=True,  # Enable state management
        )

        # Retrieve the current run details
        run = get_current_run_tree()
        run_id = run.id if run else "unknown"

        # Log the generated answer and associated run_id
        logger.info(f"Answer generated, run_id: {run_id}")
        
        # Return the response and the run_id
        return response, run_id

    async def generate_stream(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ):
        if not self.client:
            await self.initialize_client(config)

        system_message = config.get("System Message").value
        model = config.get("Model", {"value": "gpt-4o-mini"}).value

        messages = self.prepare_messages(query, context, conversation, system_message)

        try:
            logger.info(f"Generating stream response for query: {query[:50]}...")
            
            # Configure tools based on settings
            tools = []
            if config.get("Enable Web Search", {}).get("value", False):
                tools.append({"type": "web_search"})
            if config.get("Enable File Search", {}).get("value", False):
                tools.append({"type": "file_search"})
            
            # Check if this is a reasoning model that supports thinking traces
            is_reasoning_model = any(prefix in model for prefix in ["o1", "o3", "o4"])
            # o3 and o4-mini support "think with images"
            supports_image_thinking = model in ["o3", "o4-mini"]
            show_reasoning = config.get("Show Reasoning Traces", {}).get("value", True)
            enable_images = config.get("Enable Image Analysis", {}).get("value", False)
            temperature = float(config.get("Temperature", {}).get("value", "0.7"))
            
            # Add image analysis capability for o3/o4-mini
            if supports_image_thinking and enable_images:
                tools.append({"type": "image_analysis", "description": "Analyze images during thinking phase"})
            
            # Use the appropriate API based on model type
            if is_reasoning_model and show_reasoning:
                # For reasoning models, capture thinking traces
                response_stream = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                    temperature=temperature,
                    include_usage=True,
                    stream_options={"include_usage": True}
                )
            else:
                # Use standard streaming for non-reasoning models
                response_stream = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                    temperature=temperature,
                    tools=tools if not is_reasoning_model else None,  # o1 models don't support tools
                )
            
            run_id = "unknown"
            reasoning_buffer = []
            is_reasoning_phase = False
            
            async for chunk in response_stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    
                    # Check for reasoning model metadata
                    if hasattr(delta, 'reasoning') and delta.reasoning:
                        is_reasoning_phase = True
                        reasoning_buffer.append(delta.reasoning)
                        # Stream reasoning traces with special marker
                        if show_reasoning:
                            yield {
                                "message": delta.reasoning,
                                "finish_reason": None,
                                "runId": run_id,
                                "type": "reasoning",
                                "metadata": {"phase": "thinking"}
                            }
                    
                    # Handle regular content
                    if hasattr(delta, 'content') and delta.content:
                        if is_reasoning_phase and show_reasoning:
                            # Mark transition from reasoning to answer
                            yield {
                                "message": "\n---\n**Final Answer:**\n",
                                "finish_reason": None,
                                "runId": run_id,
                                "type": "transition"
                            }
                            is_reasoning_phase = False
                        
                        yield {
                            "message": delta.content,
                            "finish_reason": None,
                            "runId": run_id,
                            "type": "content"
                        }
                    
                    if hasattr(chunk.choices[0], 'finish_reason') and chunk.choices[0].finish_reason:
                        yield {
                            "message": "",
                            "finish_reason": chunk.choices[0].finish_reason,
                            "runId": run_id,
                            "reasoning_trace": reasoning_buffer if reasoning_buffer else None
                        }
                
                if hasattr(chunk, 'id'):
                    run_id = chunk.id
        except Exception as e:
            logger.error(f"Error generating stream response: {str(e)}")
            yield {"message": f"Error: {str(e)}", "finish_reason": "error", "runId": ""}

    def prepare_messages(
        self, query: str, context: str, conversation: list[dict], system_message: str
    ) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": system_message,
            }
        ]

        for message in conversation:
            messages.append({"role": message.type, "content": message.content})

        messages.append(
            {
                "role": "user",
                "content": f"Answer this query: '{query}' with this provided context: {context}",
            }
        )

        return messages