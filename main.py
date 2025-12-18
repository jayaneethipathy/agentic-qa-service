"""Main application entry point"""
import asyncio
import json
from src.cache import InMemoryCache
from src.tool_registry import ToolRegistry
from src.tools.web_search import WebSearchTool
from src.tools.weather import WeatherTool
from src.agent import AgenticQA


async def main():
    """Main application"""
    print("=" * 70)
    print(" Agentic QA Service Demo")
    print("=" * 70)
    print()
    
    # Initialize cache
    cache = InMemoryCache()
    
    # Initialize tools
    registry = ToolRegistry()
    registry.register(WebSearchTool(cache=cache))
    registry.register(WeatherTool(cache=cache))
    
    print()
    
    # Initialize agent
    agent = AgenticQA(tool_registry=registry, llm_client=None)
    
    # Example queries
    test_queries = [
        "What is the current weather in Tokyo and find the latest news about its cherry blossom season.", # Multi-tool
        "Tell me the weather for New York City.", # Parameter extraction
        "Search for latest news about quantum computing.", # Standard search
        "Find news about AI, Robotics, Space, Biology, and Physics.", # Concurrency test
        "What's the weather in Paris?" # Run twice to test cache
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 70}")
        print(f"Query {i}: {query}")
        print('─' * 70)
        
        # Execute query
        response = await agent.query(query)
        
        # Print structured JSON response
        output = {
            "answer": response.answer,
            "sources": [s.model_dump() for s in response.sources], # Updated
            "latency_ms": response.latency_ms.model_dump(),       # Updated
            "tokens": response.tokens.model_dump(),               # Updated
            "reasoning_steps": response.reasoning_steps
        }
        
        print(json.dumps(output, indent=2))
        print()
    
    print("=" * 70)
    print("✓ Demo completed successfully!")
    print("=" * 70)
    
    # Cleanup
    await registry.close_all()


if __name__ == "__main__":
    asyncio.run(main())