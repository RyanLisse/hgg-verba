import os
from dotenv import load_dotenv
from goldenverba.components.interfaces import Generator
from goldenverba.components.types import InputConfig
from goldenverba.components.util import get_environment
from anthropic import AsyncAnthropic
import logging

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class AnthropicGenerator(Generator):
    """
    Anthropic Generator using the latest Claude 4 models.
    """

    def __init__(self):
        super().__init__()
        self.name = "Anthropic"
        self.description = "Using Anthropic's Claude 4 models to generate answers to queries"
        
        # Claude 4 models support larger context windows
        self.context_window = 200000  # 200k tokens
        
        # Latest Claude models as of August 2025
        models = [
            "claude-opus-4",               # Most powerful model with precise instruction following
            "claude-sonnet-4",             # Can alternate between reasoning and tools like web search
            "claude-3.7-sonnet",           # Excellent for coding with improved memory capabilities
            "claude-opus-4-20250514",      # May 2025 release version
            "claude-sonnet-4-20250514",    # May 2025 release version
            "claude-3-7-sonnet-20250219",  # Previous 3.7 version
            "claude-3.5-sonnet-20241022",  # Previous generation
            "claude-3.5-haiku-20241022",   # Fast, cost-effective
        ]

        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[1],  # Default to Sonnet for balance
            description="Select a Claude Model",
            values=models,
        )

        if os.getenv("ANTHROPIC_API_KEY") is None:
            self.config["API Key"] = InputConfig(
                type="password",
                value="",
                description="You can set your Anthropic API Key here or set it as environment variable `ANTHROPIC_API_KEY`",
                values=[],
            )
        
        # Add configuration for Claude 4 features
        self.config["Enable Analysis Tool"] = InputConfig(
            type="bool",
            value=False,
            description="Enable Claude's analysis tool for complex reasoning",
            values=[],
        )
        
        self.config["Enable Web Search"] = InputConfig(
            type="bool",
            value=False,
            description="Enable web search for Claude Sonnet 4 (tool alternation)",
            values=[],
        )
        
        self.config["Show Reasoning Process"] = InputConfig(
            type="bool",
            value=True,
            description="Display Claude's step-by-step reasoning process",
            values=[],
        )
        
        self.config["Temperature"] = InputConfig(
            type="text",
            value="0.7",
            description="Control randomness (0.0-1.0)",
            values=[],
        )
        
        self.config["Max Tokens"] = InputConfig(
            type="number",
            value=4096,
            description="Maximum tokens in response",
            values=[],
        )
        
        # Initialize client
        self.client = None

    async def initialize_client(self, config):
        """Initialize the Anthropic client."""
        api_key = get_environment(
            config, "API Key", "ANTHROPIC_API_KEY", "No Anthropic API Key found"
        )
        
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate_stream(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ):
        """Generate streaming response using Claude 4."""
        if not self.client:
            await self.initialize_client(config)
        
        model = config.get("Model", {"value": "claude-sonnet-4"}).value
        system_message = config.get("System Message", {"value": ""}).value
        temperature = float(config.get("Temperature", {"value": 0.7}).value)
        max_tokens = int(config.get("Max Tokens", {"value": 4096}).value)
        enable_analysis = config.get("Enable Analysis Tool", {"value": False}).value
        enable_web_search = config.get("Enable Web Search", {"value": False}).value
        show_reasoning = config.get("Show Reasoning Process", {"value": True}).value
        
        messages = self.prepare_messages(query, context, conversation)
        
        # Configure tools if enabled
        tools = []
        if enable_analysis:
            tools.append({
                "type": "analysis",
                "description": "Use this tool for complex reasoning and analysis"
            })
        
        # Claude Sonnet 4 can alternate between reasoning and web search
        if enable_web_search and "sonnet-4" in model:
            tools.append({
                "type": "web_search",
                "description": "Search the web for current information"
            })
        
        # Check if this is a model with reasoning capabilities
        is_reasoning_model = any(term in model for term in ["opus-4", "sonnet-4", "3.7"])
        
        try:
            logger.info(f"Generating stream response with model: {model}")
            
            # Create message with the new SDK
            # For reasoning models, request thinking traces
            extra_params = {}
            if is_reasoning_model and show_reasoning:
                extra_params["metadata"] = {
                    "include_reasoning": True,
                    "reasoning_style": "step_by_step"
                }
            
            stream = await self.client.messages.create(
                model=model,
                messages=messages,
                system=system_message,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                tools=tools if tools else None,
                **extra_params
            )
            
            reasoning_buffer = []
            is_reasoning_phase = False
            
            async for event in stream:
                if event.type == "content_block_start":
                    # Check if this is a reasoning block
                    if hasattr(event, 'content_block') and hasattr(event.content_block, 'type'):
                        if event.content_block.type == "thinking" and show_reasoning:
                            is_reasoning_phase = True
                
                elif event.type == "content_block_delta":
                    if hasattr(event.delta, 'text'):
                        text = event.delta.text
                        
                        # Claude models may use <thinking> tags for reasoning
                        if is_reasoning_phase or ("<thinking>" in text and show_reasoning):
                            is_reasoning_phase = True
                            reasoning_buffer.append(text)
                            
                            # Stream reasoning with special formatting
                            yield {
                                "message": text,
                                "finish_reason": None,
                                "type": "reasoning",
                                "metadata": {"phase": "thinking", "model": model}
                            }
                        elif "</thinking>" in text:
                            # End of reasoning phase
                            is_reasoning_phase = False
                            # Send transition marker
                            yield {
                                "message": "\n---\n**Final Answer:**\n",
                                "finish_reason": None,
                                "type": "transition"
                            }
                        else:
                            # Regular content
                            yield {
                                "message": text,
                                "finish_reason": None,
                                "type": "content"
                            }
                
                elif event.type == "content_block_stop":
                    if is_reasoning_phase:
                        is_reasoning_phase = False
                        # Send transition if we were in reasoning phase
                        yield {
                            "message": "\n---\n**Final Answer:**\n",
                            "finish_reason": None,
                            "type": "transition"
                        }
                
                elif event.type == "message_stop":
                    yield {
                        "message": "",
                        "finish_reason": "stop",
                        "reasoning_trace": reasoning_buffer if reasoning_buffer else None
                    }
                
                elif event.type == "error":
                    yield {
                        "message": f"Error: {event.error.message}",
                        "finish_reason": "error",
                    }
                    
        except Exception as e:
            logger.error(f"Error generating stream response: {str(e)}")
            yield {
                "message": f"Error: {str(e)}",
                "finish_reason": "error",
            }

    def prepare_messages(
        self, query: str, context: str, conversation: list[dict]
    ) -> list[dict]:
        """Prepare messages in the format expected by Claude 4."""
        messages = []

        # Add conversation history
        for message in conversation:
            role = "assistant" if message.type == "system" else message.type
            messages.append({
                "role": role,
                "content": message.content,
            })

        # Add the current query with context
        # For Claude 4 models, encourage step-by-step reasoning
        prompt = f"""Answer this query: '{query}'
        
Context provided: {context}
        
For complex questions, please think through your answer step-by-step before providing the final response."""
        
        messages.append({
            "role": "user",
            "content": prompt,
        })

        return messages

    async def generate(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ) -> str:
        """Non-streaming generation method."""
        if not self.client:
            await self.initialize_client(config)
        
        model = config.get("Model", {"value": "claude-4-sonnet-20250514"}).value
        system_message = config.get("System Message", {"value": ""}).value
        temperature = float(config.get("Temperature", {"value": 0.7}).value)
        
        messages = self.prepare_messages(query, context, conversation)
        
        try:
            # Create message without streaming
            response = await self.client.messages.create(
                model=model,
                messages=messages,
                system=system_message,
                max_tokens=4096,
                temperature=temperature,
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"Error: {str(e)}"