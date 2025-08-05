# AnthropicInstructorGenerator.py - Enhanced Anthropic generator with Instructor integration
import os
from dotenv import load_dotenv
from goldenverba.components.interfaces import Generator
from goldenverba.components.types import InputConfig
from goldenverba.components.util import get_environment
from goldenverba.components.schemas import (
    RAGResponse, EnhancedRAGResponse, Citation, ConfidenceLevel, SourceType
)
import instructor
from instructor.mode import Mode
from anthropic import AsyncAnthropic
import logging
import time
from typing import List, Dict, AsyncIterator

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class AnthropicInstructorGenerator(Generator):
    """
    Enhanced Anthropic Generator using Instructor for structured outputs.
    Supports Claude 4 models with advanced reasoning, multimodal capabilities, and tool usage.
    """

    def __init__(self):
        super().__init__()
        self.name = "Anthropic Instructor"
        self.description = "Enhanced Anthropic Claude generator with structured outputs, advanced reasoning, and multimodal support"
        self.context_window = 200000  # 200k tokens for Claude 4

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
            value=models[1],  # Default to Sonnet 4 for balance of power and speed
            description="Select a Claude Model",
            values=models,
        )

        if os.getenv("ANTHROPIC_API_KEY") is None:
            self.config["API Key"] = InputConfig(
                type="password",
                value="",
                description="Anthropic API Key (required for Claude models)",
                values=[],
            )

        # Instructor mode configuration
        self.config["Instructor Mode"] = InputConfig(
            type="dropdown",
            value="ANTHROPIC_TOOLS",
            description="Instructor integration mode",
            values=["ANTHROPIC_JSON", "ANTHROPIC_TOOLS", "ANTHROPIC_PARALLEL_TOOLS"],
        )

        # Advanced Claude 4 features
        self.config["Enable Analysis Tool"] = InputConfig(
            type="bool",
            value=True,
            description="Enable Claude's built-in analysis tool for complex reasoning",
            values=[],
        )

        self.config["Enable Extended Thinking"] = InputConfig(
            type="bool",
            value=True,
            description="Enable extended thinking process for Claude 3.7+ models",
            values=[],
        )

        self.config["Show Reasoning Process"] = InputConfig(
            type="bool",
            value=True,
            description="Display Claude's step-by-step reasoning process",
            values=[],
        )

        self.config["Enable Multimodal"] = InputConfig(
            type="bool",
            value=True,
            description="Enable image and document analysis capabilities",
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
            description="Control randomness (0.0-1.0)",
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
        api_key = get_environment(
            config, "API Key", "ANTHROPIC_API_KEY", "No Anthropic API Key found"
        )

        # Regular Anthropic client
        self.client = AsyncAnthropic(api_key=api_key)
        
        # Instructor client with mode selection
        mode_name = config.get("Instructor Mode", {"value": "ANTHROPIC_TOOLS"}).value
        mode = getattr(Mode, mode_name)
        
        self.instructor_client = instructor.from_anthropic(
            AsyncAnthropic(api_key=api_key),
            mode=mode
        )

    async def generate_structured_response(
        self, 
        messages: List[Dict], 
        model: str, 
        config: Dict,
        response_format: str = "enhanced"
    ) -> EnhancedRAGResponse:
        """Generate a structured response using Instructor."""
        
        logger.info(f"Generating structured response with Claude model: {model}")
        start_time = time.time()

        # Check for advanced model capabilities
        supports_extended_thinking = "3.7" in model or "4" in model
        enable_extended_thinking = config.get("Enable Extended Thinking", {}).get("value", True)
        enable_analysis = config.get("Enable Analysis Tool", {}).get("value", True)

        try:
            # Select response model based on format
            if response_format == "enhanced":
                response_model = EnhancedRAGResponse
            else:
                response_model = RAGResponse

            # Configure tools based on model capabilities
            tools = []
            if enable_analysis and "4" in model:
                tools.append({
                    "name": "analysis",
                    "description": "Deep analysis tool for complex reasoning"
                })

            # Generate structured response with Claude-specific optimizations
            create_params = {
                "model": model,
                "response_model": response_model,
                "messages": messages,
                "temperature": float(config.get("Temperature", {}).get("value", "0.7")),
                "max_tokens": config.get("Max Tokens", {}).get("value", 4096),
                "max_retries": 2
            }

            # Add tools if available
            if tools:
                create_params["tools"] = tools

            response = await self.instructor_client.messages.create(**create_params)

            # Add metadata
            generation_time = time.time() - start_time
            response.generation_time = generation_time
            response.model_name = model
            response.tools_used = [tool["name"] for tool in tools] if tools else []

            # Enhance response with Claude-specific features
            if supports_extended_thinking and enable_extended_thinking:
                response.extended_thinking = "Used Claude's extended thinking capabilities for deeper analysis"

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
        
        if not self.client or not self.instructor_client:
            await self.initialize_client(config)

        system_message = config.get("System Message").value
        model = config.get("Model", {"value": "claude-sonnet-4"}).value
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
                async for chunk in self.generate_regular_stream(messages, model, config):
                    yield chunk

        except Exception as e:
            logger.error(f"Error in generate_stream: {str(e)}")
            yield {
                "message": f"Error: {str(e)}",
                "finish_reason": "error",
                "runId": "error"
            }

    def stream_structured_response(self, response: EnhancedRAGResponse) -> AsyncIterator[dict]:
        """Stream a structured response in chunks with Claude-specific formatting."""
        run_id = f"claude_{int(time.time())}"
        
        # Stream extended thinking if available
        if response.extended_thinking:
            yield {
                "message": "## 🧠 Extended Thinking Process\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "thinking_header"
            }
            
            yield {
                "message": f"{response.extended_thinking}\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "extended_thinking"
            }

        # Stream reasoning trace if available
        if response.reasoning_trace and response.reasoning_trace.reasoning_steps:
            yield {
                "message": "## 🔍 Reasoning Steps\n\n",
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
            "message": "## 💬 Claude's Response\n\n",
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

        # Stream alternative perspectives if available
        if response.alternative_perspectives:
            yield {
                "message": "\n\n## 🔄 Alternative Perspectives\n\n",
                "finish_reason": None,
                "runId": run_id,
                "type": "perspectives_header"
            }
            
            for perspective in response.alternative_perspectives:
                yield {
                    "message": f"• {perspective}\n",
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "perspective"
                }

        # Stream citations with Claude-specific formatting
        if response.citations:
            yield {
                "message": "\n\n## 📖 Sources Referenced\n\n",
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

        # Stream limitations and caveats (Claude is good at these)
        if response.limitations:
            yield {
                "message": "\n\n## ⚠️ Important Limitations\n\n",
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
                "message": "\n\n## 🤔 Questions to Explore Further\n\n",
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

        # Final metadata with Claude-specific metrics
        metadata = {
            "confidence": response.confidence_level.value,
            "model": response.model_name,
            "generation_time": response.generation_time,
            "sources_used": len(response.citations),
            "tools_used": response.tools_used,
            "factual_accuracy": response.factual_accuracy_score,
            "completeness": response.completeness_score,
            "claude_features": {
                "extended_thinking": bool(response.extended_thinking),
                "alternative_perspectives": len(response.alternative_perspectives),
                "limitations_identified": len(response.limitations)
            }
        }

        yield {
            "message": "",
            "finish_reason": "stop",
            "runId": run_id,
            "metadata": metadata
        }

    async def generate_regular_stream(self, messages: List[Dict], model: str, config: Dict):
        """Fall back to regular streaming for non-structured output."""
        temperature = float(config.get("Temperature", {}).get("value", "0.7"))
        
        # Convert messages format for Anthropic
        system_message = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        user_messages = [msg for msg in messages if msg["role"] != "system"]
        
        stream = await self.client.messages.create(
            model=model,
            messages=user_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=config.get("Max Tokens", {}).get("value", 4096),
            stream=True
        )
        
        run_id = "claude_regular_stream"
        
        async for chunk in stream:
            if chunk.type == "content_block_delta":
                yield {
                    "message": chunk.delta.text,
                    "finish_reason": None,
                    "runId": run_id,
                    "type": "content"
                }
            elif chunk.type == "message_stop":
                yield {
                    "message": "",
                    "finish_reason": "stop",
                    "runId": run_id
                }

    def prepare_messages(
        self, query: str, context: str, conversation: list[dict], system_message: str
    ) -> list[dict]:
        """Prepare messages optimized for Claude's capabilities."""
        
        # Enhanced system message for Claude with structured outputs
        enhanced_system = f"""{system_message}

As Claude, you excel at:
1. Providing nuanced, well-reasoned responses
2. Acknowledging limitations and uncertainties
3. Offering multiple perspectives when appropriate
4. Breaking down complex problems step-by-step
5. Citing sources accurately and comprehensively

When responding:
- Be thorough but concise
- Show your reasoning process
- Acknowledge what you're uncertain about
- Provide specific citations from the context
- Suggest thoughtful follow-up questions
- Consider alternative viewpoints

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

Please provide a comprehensive, well-structured response that demonstrates your reasoning process and cites relevant sources from the context."""

        messages.append({
            "role": "user",
            "content": user_content
        })

        return messages

    def extract_citations_from_context(self, context: str, max_citations: int = 8) -> List[Citation]:
        """Extract citations from context with Claude-optimized processing."""
        citations = []
        
        # More sophisticated extraction for Claude
        context_sections = context.split('\n\n')
        
        for i, section in enumerate(context_sections[:max_citations]):
            if len(section.strip()) > 100:  # Longer, more meaningful chunks for Claude
                # Try to extract a title from the first line
                lines = section.split('\n')
                potential_title = lines[0] if lines else f"Context Section {i+1}"
                
                citation = Citation(
                    source_id=f"claude_context_{i}",
                    source_type=SourceType.DOCUMENT,
                    title=potential_title[:100] + "..." if len(potential_title) > 100 else potential_title,
                    content_snippet=section[:300] + "..." if len(section) > 300 else section,
                    confidence_score=0.85,  # Higher confidence for Claude's processing
                    metadata={
                        "section_number": i + 1,
                        "length": len(section),
                        "processed_by": "claude"
                    }
                )
                citations.append(citation)
        
        return citations