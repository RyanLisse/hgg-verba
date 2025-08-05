#!/usr/bin/env python3
"""
Test script to verify the reasoning trace functionality for OpenAI and Gemini generators.
"""

import asyncio
import os
import pytest
from dotenv import load_dotenv

# Skip imports if running as pytest due to missing dependencies
try:
    from goldenverba.components.generation.OpenAIGenerator import OpenAIGenerator
    from goldenverba.components.generation.GeminiGenerator import GeminiGenerator
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

load_dotenv()

@pytest.mark.asyncio
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="goldenverba components not available")
async def test_openai_generator():
    """Test OpenAI generator with reasoning models."""
    print("\n" + "="*50)
    print("Testing OpenAI Generator with Reasoning")
    print("="*50)
    
    generator = OpenAIGenerator()
    
    # Configure for reasoning model
    config = {
        "Model": {"value": "o1-preview"},  # Use reasoning model
        "Show Reasoning Traces": {"value": True},
        "Temperature": {"value": 0.7},
        "System Message": {"value": "You are a helpful assistant that explains your reasoning."}
    }
    
    # Set API key if available
    if os.getenv("OPENAI_API_KEY"):
        config["API Key"] = {"value": os.getenv("OPENAI_API_KEY")}
    
    query = "What is the capital of France and why is it important?"
    context = "France is a country in Western Europe."
    
    print(f"\nQuery: {query}")
    print(f"Context: {context}")
    print("\nGenerating response with reasoning traces...\n")
    
    try:
        reasoning_steps = []
        response_content = ""
        
        async for chunk in generator.generate_stream(config, query, context, []):
            if chunk.get("type") == "reasoning":
                reasoning_steps.append(chunk["message"])
                print(f"🤔 Reasoning: {chunk['message']}")
            elif chunk.get("type") == "transition":
                print(chunk["message"])
            elif chunk.get("type") == "content":
                response_content += chunk["message"]
                print(chunk["message"], end="", flush=True)
            
            if chunk.get("finish_reason") == "stop":
                print("\n\n" + "="*30)
                print(f"Complete Response: {response_content}")
                if chunk.get("reasoning_trace"):
                    print(f"Reasoning Steps: {len(chunk['reasoning_trace'])}")
                break
                
    except Exception as e:
        print(f"Error: {e}")

@pytest.mark.asyncio
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="goldenverba components not available")
async def test_gemini_generator():
    """Test Gemini generator with thinking models."""
    print("\n" + "="*50)
    print("Testing Gemini Generator with Thinking")
    print("="*50)
    
    generator = GeminiGenerator()
    
    # Configure for thinking model
    config = {
        "Model": {"value": "gemini-2.0-flash-thinking-exp-0827"},  # Use thinking model
        "Show Thinking Process": {"value": True},
        "Temperature": {"value": 0.7},
        "Max Output Tokens": {"value": 2048},
        "System Message": {"value": "You are a helpful assistant that thinks step by step."}
    }
    
    query = "What is 25 * 37 and how did you calculate it?"
    context = "Please show your calculation steps."
    
    print(f"\nQuery: {query}")
    print(f"Context: {context}")
    print("\nGenerating response with thinking process...\n")
    
    try:
        thinking_steps = []
        response_content = ""
        
        async for chunk in generator.generate_stream(config, query, context, []):
            if chunk.get("type") == "thinking":
                thinking_steps.append(chunk["message"])
                print(f"🤔 {chunk['message']}")
            elif chunk.get("type") == "transition":
                print(chunk["message"])
            elif chunk.get("type") == "content":
                response_content += chunk["message"]
                print(chunk["message"], end="", flush=True)
            
            if chunk.get("finish_reason") == "stop":
                print("\n\n" + "="*30)
                print(f"Complete Response: {response_content}")
                if chunk.get("thinking_trace"):
                    print(f"Thinking Steps: {len(chunk['thinking_trace'])}")
                break
                
    except Exception as e:
        print(f"Error: {e}")

@pytest.mark.asyncio
@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="goldenverba components not available")
async def test_main():
    """Run tests for both generators."""
    print("\n" + "🚀 "*20)
    print("TESTING REASONING/THINKING TRACE FUNCTIONALITY")
    print("🚀 "*20)
    
    # Test OpenAI if API key is available
    if os.getenv("OPENAI_API_KEY"):
        await test_openai_generator()
    else:
        print("\n⚠️  Skipping OpenAI test - OPENAI_API_KEY not set")
    
    # Test Gemini if API key is available
    if os.getenv("GOOGLE_API_KEY"):
        await test_gemini_generator()
    else:
        print("\n⚠️  Skipping Gemini test - GOOGLE_API_KEY not set")
    
    print("\n" + "✅ "*20)
    print("TESTING COMPLETE")
    print("✅ "*20)


async def main():
    """Main function for standalone script execution."""
    await test_main()

if __name__ == "__main__":
    asyncio.run(main())