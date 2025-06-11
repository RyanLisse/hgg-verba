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
        
        # Latest Claude models as of June 2025
        models = [
            "claude-opus-4-20250514",      # Most capable model for coding and complex tasks
            "claude-sonnet-4-20250514",    # High-performance with exceptional reasoning
            "claude-3-7-sonnet-20250219",  # First hybrid reasoning model with thinking
            "claude-3-7-sonnet-latest",    # Alias for latest 3.7 sonnet
            "claude-3-5-haiku",            # Fast, cost-effective for simple tasks
            "claude-3-5-sonnet",           # Previous generation balanced model
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
        
        self.config["Temperature"] = InputConfig(
            type="number",
            value=0.7,
            description="Control randomness (0.0-1.0)",
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
        
        model = config.get("Model", {"value": "claude-4-sonnet-20250514"}).value
        system_message = config.get("System Message", {"value": ""}).value
        temperature = float(config.get("Temperature", {"value": 0.7}).value)
        enable_analysis = config.get("Enable Analysis Tool", {"value": False}).value
        
        messages = self.prepare_messages(query, context, conversation)
        
        # Configure tools if enabled
        tools = []
        if enable_analysis:
            tools.append({
                "type": "analysis",
                "description": "Use this tool for complex reasoning and analysis"
            })
        
        try:
            logger.info(f"Generating stream response with model: {model}")
            
            # Create message with the new SDK
            stream = await self.client.messages.create(
                model=model,
                messages=messages,
                system=system_message,
                max_tokens=4096,
                temperature=temperature,
                stream=True,
                tools=tools if tools else None,
            )
            
            async for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, 'text'):
                        yield {
                            "message": event.delta.text,
                            "finish_reason": None,
                        }
                elif event.type == "message_stop":
                    yield {
                        "message": "",
                        "finish_reason": "stop",
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
        messages.append({
            "role": "user",
            "content": f"Answer this query: '{query}' with this provided context: {context}",
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