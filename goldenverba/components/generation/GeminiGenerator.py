import os
from typing import List, Dict, AsyncIterator

try:
    from google import genai
    from google.genai.types import HttpOptions, Content, Part
except ImportError:
    genai = None
    pass

from wasabi import msg
from dotenv import load_dotenv

from goldenverba.components.interfaces import Generator
from goldenverba.components.types import InputConfig

load_dotenv()


class GeminiGenerator(Generator):
    """
    Gemini Generator using the new google.genai client.
    """

    def __init__(self):
        super().__init__()
        self.name = "Gemini"
        self.description = "Generator using Google's Gemini models via the new genai client"
        self.requires_library = ["google-genai"]
        self.requires_env = [
            "GOOGLE_API_KEY",  # Changed from GOOGLE_APPLICATION_CREDENTIALS
        ]
        self.streamable = True
        
        # Available Gemini models as of July 2025
        models = [
            "gemini-2.5-pro-latest",            # Latest 2.5 Pro release
            "gemini-2.5-flash-latest",          # Latest 2.5 Flash release
            "gemini-2.5-pro-experimental",      # Experimental 2.5 Pro model
            "gemini-2.5-flash-preview-05-20",   # Previous preview version
            "gemini-2.0-flash",                 # Multimodal with next-gen features
            "gemini-2.0-flash-lite",            # Optimized for cost efficiency
            "gemini-1.5-pro-002",               # Legacy stable model
            "gemini-1.5-flash-002",             # Legacy fast model
        ]
        
        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[0],
            description="Select a Gemini Model",
            values=models,
        )
        
        # Gemini models support up to 2M tokens context window
        self.context_window = 1000000  # 1M tokens for safety
        
        # Initialize client
        self.client = None

    def initialize_client(self, config: dict):
        """Initialize the Google genai client."""
        if genai is None:
            raise ImportError("google-genai library is not installed. Please install it with: pip install google-genai")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        # Initialize client with HTTP options
        self.client = genai.Client(
            api_key=api_key,
            http_options=HttpOptions(api_version="v1")
        )

    async def generate_stream(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ) -> AsyncIterator[dict]:
        """Generate a stream of response dicts based on query and context.
        
        @parameter: config : dict - Configuration settings
        @parameter: query : str - User query
        @parameter: context : str - Context information
        @parameter: conversation : list[dict] - Conversation history
        @returns AsyncIterator[dict] - Token response stream
        """
        
        if self.client is None:
            self.initialize_client(config)
        
        model = config.get("Model", {"value": "gemini-2.5-pro-latest"}).value
        system_message = config.get("System Message", {"value": ""}).value
        
        # Prepare the content
        contents = self.prepare_contents(query, context, conversation, system_message)
        
        try:
            # Generate content using the new client
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                stream=True,  # Enable streaming
            )
            
            # Stream the response
            async for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield {
                        "message": chunk.text,
                        "finish_reason": None,
                    }
            
            # Final message to indicate completion
            yield {
                "message": "",
                "finish_reason": "stop",
            }
            
        except Exception as e:
            msg.fail(f"Error generating response: {str(e)}")
            yield {
                "message": f"Error: {str(e)}",
                "finish_reason": "error",
            }

    def prepare_contents(
        self, query: str, context: str, conversation: list[dict], system_message: str
    ) -> str:
        """
        Prepares the content string for the Gemini model.
        
        @parameter query: User query to be answered
        @parameter context: Context information provided
        @parameter conversation: Previous conversation messages
        @parameter system_message: System instructions
        
        @returns: Formatted content string for the model
        """
        # Build the full prompt
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append(f"System: {system_message}")
        
        # Add conversation history
        for message in conversation:
            role = "Human" if message.type == "user" else "Assistant"
            messages.append(f"{role}: {message.content}")
        
        # Add context and query
        messages.append(f"Context: {context}")
        messages.append(f"Human: {query}")
        messages.append("Assistant:")
        
        # Join all messages into a single string
        return "\n\n".join(messages)

    async def generate(
        self,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict] = [],
    ) -> str:
        """Non-streaming generation method."""
        if self.client is None:
            self.initialize_client(config)
        
        model = config.get("Model", {"value": "gemini-2.5-pro-latest"}).value
        system_message = config.get("System Message", {"value": ""}).value
        
        # Prepare the content
        contents = self.prepare_contents(query, context, conversation, system_message)
        
        try:
            # Generate content using the new client (non-streaming)
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
            )
            
            return response.text
            
        except Exception as e:
            msg.fail(f"Error generating response: {str(e)}")
            return f"Error: {str(e)}"