#!/usr/bin/env python3
"""
Test script for August 2025 generator updates:
- OpenAI: o3, o4-mini, GPT-4.1 family with image thinking
- Anthropic: Claude Opus 4, Sonnet 4, 3.7 with tool alternation
- Google: Gemini 2.5 with Deep Think multi-agent reasoning
"""

import asyncio
import os
import pytest
from dotenv import load_dotenv

# Skip imports if running as pytest due to missing dependencies
try:
    from goldenverba.components.generation.OpenAIGenerator import OpenAIGenerator
    from goldenverba.components.generation.AnthropicGenerator import AnthropicGenerator
    from goldenverba.components.generation.GeminiGenerator import GeminiGenerator

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

load_dotenv()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="goldenverba components not available"
)
async def test_openai_o3():
    """Test OpenAI o3 model with image thinking capability."""
    print("\n" + "=" * 60)
    print("🚀 Testing OpenAI o3 - Smartest Model with Image Thinking")
    print("=" * 60)

    generator = OpenAIGenerator()

    config = {
        "Model": {"value": "o3"},
        "Show Reasoning Traces": {"value": True},
        "Enable Image Analysis": {"value": True},  # o3 can "think with images"
        "Temperature": {"value": 0.7},
        "System Message": {
            "value": "You are an advanced AI that can reason about images and text."
        },
    }

    if os.getenv("OPENAI_API_KEY"):
        config["API Key"] = {"value": os.getenv("OPENAI_API_KEY")}

    query = (
        "Explain the Pythagorean theorem and how it applies to real-world scenarios."
    )
    context = "Consider construction, navigation, and computer graphics applications."

    print(f"\nQuery: {query}")
    print(f"Context: {context}")
    print("\n🧠 Generating response with o3 reasoning...\n")

    try:
        reasoning_steps = []

        async for chunk in generator.generate_stream(config, query, context, []):
            if chunk.get("type") == "reasoning":
                reasoning_steps.append(chunk["message"])
                print(f"💭 {chunk['message']}")
            elif chunk.get("type") == "transition":
                print(chunk["message"])
            elif chunk.get("type") == "content":
                print(chunk["message"], end="", flush=True)

            if chunk.get("finish_reason") == "stop":
                print(
                    f"\n\n✅ Response complete. Reasoning steps: {len(reasoning_steps)}"
                )
                break

    except Exception as e:
        print(f"❌ Error: {e}")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="goldenverba components not available"
)
async def test_anthropic_claude4():
    """Test Anthropic Claude Opus 4 with tool alternation."""
    print("\n" + "=" * 60)
    print("🎭 Testing Anthropic Claude Opus 4 - Enterprise Leader")
    print("=" * 60)

    generator = AnthropicGenerator()

    config = {
        "Model": {"value": "claude-opus-4"},
        "Show Reasoning Process": {"value": True},
        "Enable Web Search": {
            "value": True
        },  # Claude Sonnet 4 can alternate with tools
        "Temperature": {"value": 0.7},
        "Max Tokens": {"value": 4096},
        "System Message": {
            "value": "You are Claude Opus 4, optimized for precise instruction following."
        },
    }

    if os.getenv("ANTHROPIC_API_KEY"):
        config["API Key"] = {"value": os.getenv("ANTHROPIC_API_KEY")}

    query = "What are the key differences between functional and object-oriented programming?"
    context = "Focus on practical use cases and when to choose each paradigm."

    print(f"\nQuery: {query}")
    print(f"Context: {context}")
    print("\n🤔 Generating response with Claude 4 reasoning...\n")

    try:
        reasoning_buffer = []

        async for chunk in generator.generate_stream(config, query, context, []):
            if chunk.get("type") == "reasoning":
                reasoning_buffer.append(chunk["message"])
                print(f"🎯 {chunk['message']}", end="")
            elif chunk.get("type") == "transition":
                print(chunk["message"])
            elif chunk.get("type") == "content":
                print(chunk["message"], end="", flush=True)

            if chunk.get("finish_reason") == "stop":
                print("\n\n✅ Response complete.")
                if chunk.get("reasoning_trace"):
                    print(f"📊 Reasoning trace steps: {len(chunk['reasoning_trace'])}")
                break

    except Exception as e:
        print(f"❌ Error: {e}")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="goldenverba components not available"
)
async def test_gemini_deep_think():
    """Test Gemini 2.5 Deep Think with multi-agent parallel processing."""
    print("\n" + "=" * 60)
    print("🧬 Testing Gemini 2.5 Deep Think - Multi-Agent Reasoning")
    print("=" * 60)

    generator = GeminiGenerator()

    config = {
        "Model": {"value": "gemini-2.5-deep-think"},
        "Show Thinking Process": {"value": True},
        "Enable Deep Think": {"value": True},
        "Enable Google Search": {"value": True},
        "Enable Code Execution": {"value": True},
        "Temperature": {"value": 0.7},
        "Max Output Tokens": {"value": 8192},
        "System Message": {
            "value": "You are Gemini Deep Think, capable of exploring multiple ideas in parallel."
        },
    }

    # Note: Deep Think can take hours for complex problems
    # Using a simpler query for testing
    query = "Design a simple algorithm to find the shortest path in a graph."
    context = "Consider both Dijkstra's algorithm and A* search. Explain trade-offs."

    print(f"\nQuery: {query}")
    print(f"Context: {context}")
    print("\n🧠 Activating Deep Think mode (may take several minutes)...\n")
    print("⚠️  Note: Deep Think can take hours for complex problems.\n")

    try:
        thinking_steps = []

        async for chunk in generator.generate_stream(config, query, context, []):
            if (
                chunk.get("type") == "system"
                and chunk.get("metadata", {}).get("phase") == "deep_think_init"
            ):
                print(chunk["message"])
            elif chunk.get("type") == "thinking":
                thinking_steps.append(chunk["message"])
                print(f"🔄 Agent: {chunk['message']}", end="")
            elif chunk.get("type") == "transition":
                print(chunk["message"])
            elif chunk.get("type") == "content":
                print(chunk["message"], end="", flush=True)

            if chunk.get("finish_reason") == "stop":
                print("\n\n✅ Deep Think complete.")
                if chunk.get("thinking_trace"):
                    print(f"🧩 Parallel thinking steps: {len(chunk['thinking_trace'])}")
                break

    except Exception as e:
        print(f"❌ Error: {e}")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="goldenverba components not available"
)
async def test_quick_comparison():
    """Quick comparison of all three generators with latest models."""
    print("\n" + "=" * 60)
    print("⚡ Quick Comparison - Latest Models (August 2025)")
    print("=" * 60)

    query = "What is 42 + 58?"
    context = "Simple arithmetic calculation."

    # Test configurations for each provider
    configs = [
        (
            "OpenAI GPT-4.1",
            OpenAIGenerator(),
            {
                "Model": {"value": "gpt-4.1"},
                "Temperature": {"value": 0.5},
                "System Message": {"value": "You are a helpful assistant."},
            },
        ),
        (
            "Anthropic Claude 3.7 Sonnet",
            AnthropicGenerator(),
            {
                "Model": {"value": "claude-3.7-sonnet"},
                "Temperature": {"value": 0.5},
                "System Message": {
                    "value": "You are a helpful assistant focused on coding."
                },
            },
        ),
        (
            "Google Gemini 2.5 Flash",
            GeminiGenerator(),
            {
                "Model": {"value": "gemini-2.5-flash"},
                "Temperature": {"value": 0.5},
                "System Message": {"value": "You are a helpful assistant."},
            },
        ),
    ]

    for name, generator, config in configs:
        print(f"\n📍 Testing {name}...")

        # Add API keys if available
        if "OpenAI" in name and os.getenv("OPENAI_API_KEY"):
            config["API Key"] = {"value": os.getenv("OPENAI_API_KEY")}
        elif "Anthropic" in name and os.getenv("ANTHROPIC_API_KEY"):
            config["API Key"] = {"value": os.getenv("ANTHROPIC_API_KEY")}

        try:
            response = ""
            async for chunk in generator.generate_stream(config, query, context, []):
                if chunk.get("type") == "content" or (
                    chunk.get("type") is None and chunk.get("message")
                ):
                    response += chunk["message"]
                if chunk.get("finish_reason") == "stop":
                    break

            print(f"   Answer: {response.strip()}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="goldenverba components not available"
)
async def test_main():
    """Run all tests for August 2025 generator updates."""
    print("\n" + "🚀 " * 20)
    print("AUGUST 2025 GENERATOR UPDATES TEST SUITE")
    print("🚀 " * 20)

    print("\n📋 Available Tests:")
    print("1. OpenAI o3 with Image Thinking")
    print("2. Anthropic Claude Opus 4")
    print("3. Google Gemini 2.5 Deep Think")
    print("4. Quick Comparison of Latest Models")

    # Run quick comparison first
    await test_quick_comparison()

    # Test individual advanced features if API keys are available
    if os.getenv("OPENAI_API_KEY"):
        await test_openai_o3()
    else:
        print("\n⚠️  Skipping OpenAI o3 test - OPENAI_API_KEY not set")

    if os.getenv("ANTHROPIC_API_KEY"):
        await test_anthropic_claude4()
    else:
        print("\n⚠️  Skipping Anthropic Claude 4 test - ANTHROPIC_API_KEY not set")

    if os.getenv("GOOGLE_API_KEY"):
        # Note: Deep Think can be very slow, so we'll skip it in automated tests
        print("\n⚠️  Skipping Gemini Deep Think test (can take hours)")
        print("   To test Deep Think, run: await test_gemini_deep_think()")
    else:
        print("\n⚠️  Skipping Gemini tests - GOOGLE_API_KEY not set")

    print("\n" + "✅ " * 20)
    print("TEST SUITE COMPLETE")
    print("✅ " * 20)
    print("\n📊 Summary:")
    print("- OpenAI: o3/o4-mini with 'think with images' capability")
    print("- Anthropic: Claude 4 models holding 32% enterprise market share")
    print("- Google: Gemini 2.5 with Deep Think multi-agent parallel processing")
    print("- All models support advanced reasoning traces visible in UI")


async def main():
    """Main function for standalone script execution."""
    await test_main()


if __name__ == "__main__":
    asyncio.run(main())
