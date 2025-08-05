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
        
        # Available Gemini models as of August 2025
        models = [
            "gemini-2.0-flash-thinking-exp-0827",  # Latest thinking model with explicit reasoning
            "gemini-2.0-pro-exp-0827",             # Most advanced pro model
            "gemini-1.5-pro-exp-0827",             # Updated pro with 2M context
            "gemini-1.5-flash-exp-0827",           # Fast model with thinking traces
            "gemini-1.5-flash-8b-exp-0827",        # Efficient 8B parameter model
            "gemini-2.0-flash",                    # Stable multimodal model
            "gemini-2.0-flash-lite",               # Cost-optimized model
            "gemini-1.5-pro-002",                  # Previous stable version
            "gemini-1.5-flash-002",                # Previous fast version
        ]
        
        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[0],
            description="Select a Gemini Model",
            values=models,
        )
        
        # Gemini models support up to 2M tokens context window
        self.context_window = 2000000  # 2M tokens for latest models
        
        # Add configuration for thinking/reasoning features
        self.config["Show Thinking Process"] = InputConfig(
            type="bool",
            value=True,
            description="Display step-by-step thinking process for thinking models",
            values=[],
        )
        
        self.config["Temperature"] = InputConfig(
            type="number",
            value=0.7,
            description="Temperature for response generation (0.0-2.0)",
            values=[],
        )
        
        self.config["Max Output Tokens"] = InputConfig(
            type="number",
            value=8192,
            description="Maximum number of tokens in the response",
            values=[],
        )
        
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
        
        model = config.get("Model", {"value": "gemini-2.5-flash-preview-05-20"}).value
        system_message = config.get("System Message", {"value": ""}).value
        
        # Prepare the content
        contents = self.prepare_contents(query, context, conversation, system_message)
        
        # Check if this is a thinking model
        is_thinking_model = "thinking" in model.lower()
        show_thinking = config.get("Show Thinking Process", {}).get("value", True)
        temperature = config.get("Temperature", {}).get("value", 0.7)
        max_tokens = config.get("Max Output Tokens", {}).get("value", 8192)
        
        try:
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "candidate_count": 1,
            }
            
            # For thinking models, we'll parse the response differently
            if is_thinking_model and show_thinking:
                # Add instructions to show thinking process
                contents = contents.replace(
                    "Assistant:",
                    "Assistant (show your step-by-step thinking process):"
                )
            
            # Generate content using the new client
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                generation_config=generation_config,
                stream=True,  # Enable streaming
            )
            
            # Stream the response
            thinking_steps = []
            is_thinking_phase = False
            accumulated_text = ""
            
            async for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    accumulated_text += chunk.text
                    
                    # For thinking models, detect and parse thinking patterns
                    if is_thinking_model and show_thinking:
                        # Look for thinking markers in the text
                        if "<thinking>" in chunk.text or "Step " in chunk.text or "First," in chunk.text:
                            is_thinking_phase = True
                        
                        if is_thinking_phase and ("</thinking>" in chunk.text or "Final answer:" in chunk.text or "Therefore," in chunk.text):
                            # Transition from thinking to answer
                            parts = chunk.text.split("</thinking>")
                            if len(parts) > 1:
                                thinking_part = parts[0]
                                answer_part = parts[1]
                                
                                # Stream thinking part
                                if thinking_part:
                                    thinking_steps.append(thinking_part)
                                    yield {
                                        "message": f"🤔 {thinking_part}\n",
                                        "finish_reason": None,
                                        "type": "thinking",
                                        "metadata": {"phase": "reasoning"}
                                    }
                                
                                # Transition marker
                                yield {
                                    "message": "\n---\n**Final Answer:**\n",
                                    "finish_reason": None,
                                    "type": "transition"
                                }
                                
                                # Stream answer part
                                if answer_part:
                                    yield {
                                        "message": answer_part,
                                        "finish_reason": None,
                                        "type": "content"
                                    }
                                is_thinking_phase = False
                            else:
                                # Still in thinking phase
                                thinking_steps.append(chunk.text)
                                yield {
                                    "message": f"🤔 {chunk.text}",
                                    "finish_reason": None,
                                    "type": "thinking",
                                    "metadata": {"phase": "reasoning"}
                                }
                        else:
                            # Regular content or answer phase
                            yield {
                                "message": chunk.text,
                                "finish_reason": None,
                                "type": "content" if not is_thinking_phase else "thinking"
                            }
                    else:
                        # Regular streaming for non-thinking models
                        yield {
                            "message": chunk.text,
                            "finish_reason": None,
                            "type": "content"
                        }
            
            # Final message to indicate completion
            yield {
                "message": "",
                "finish_reason": "stop",
                "thinking_trace": thinking_steps if thinking_steps else None
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
        
        # Enhanced system message for thinking models
        if system_message:
            messages.append(f"System: {system_message}")
            messages.append("You are an advanced AI assistant capable of step-by-step reasoning. When answering complex questions, break down your thinking process into clear steps.")
        
        # Add conversation history
        for message in conversation:
            role = "Human" if message.type == "user" else "Assistant"
            messages.append(f"{role}: {message.content}")
        
        # Add context and query with reasoning instructions
        messages.append(f"Context: {context}")
        messages.append(f"Human: {query}")
        messages.append("Please think through this step-by-step before providing your answer.")
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
        
        model = config.get("Model", {"value": "gemini-2.5-flash-preview-05-20"}).value
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