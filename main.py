"""Main application entry point"""
import asyncio
import json
import sys
from src.cache import InMemoryCache
from src.tool_registry import ToolRegistry
from src.tools.web_search import WebSearchTool
from src.tools.weather import WeatherTool
from src.tools.calculator import CalculatorTool
from src.agent import AgenticQA
from src.policy import PolicyEnforcer


async def main():
    """Main application"""
    print("=" * 70)
    print("🤖 Agentic QA Service Demo")
    print("=" * 70)
    print()
    
    # Initialize cache
    cache = InMemoryCache()
    
    # Initialize policy
    policy = PolicyEnforcer()
    
    # Initialize tools
    print("📦 Initializing tools...")
    registry = ToolRegistry()
    registry.register(WebSearchTool(cache=cache))
    registry.register(WeatherTool(cache=cache))
    registry.register(CalculatorTool(cache=cache))
    
    print()
    
    # Initialize agent - FIXED: removed llm_client parameter
    agent = AgenticQA(
        tool_registry=registry,
        policy=policy,
        max_concurrent_tools=3
    )
    
    # Example queries
    test_queries = [
        "What is the current weather in Tokyo and find the latest news about its cherry blossom season.", # Multi-tool
        "Tell me the weather for New York City.", # Parameter extraction
        "Search for latest news about quantum computing.", # Standard search
        "Find news about AI, Robotics, Space, Biology, and Physics.", # Concurrency test
        "What's the weather in Paris?" # Run twice to test cache
        "Calculate 15 * 234 + 567"
    ]
    
    print(f"🎬 Running {len(test_queries)} demo queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"{'─' * 70}")
        print(f"Query {i}/{len(test_queries)}: {query}")
        print('─' * 70)
        
        try:
            # Execute query
            response = await agent.query(query)
            
            # Print structured JSON response
            output = {
                "answer": response.answer,
                "sources": [s.dict() for s in response.sources],
                "latency_ms": response.latency_ms.dict(),
                "tokens": response.tokens.dict(),
                "cost": response.cost.dict() if response.cost else None,
                "reasoning_steps": response.reasoning_steps
            }
            
            print(json.dumps(output, indent=2))
            print()
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 70)
    print("✅ Demo completed successfully!")
    print("=" * 70)
    
    # Show cache statistics
    print("\n📊 Cache Statistics:")
    stats = cache.get_stats()
    print(f"   • Cache Hits: {stats['hits']}")
    print(f"   • Cache Misses: {stats['misses']}")
    print(f"   • Hit Rate: {stats['hit_rate']:.1%}")
    print(f"   • Total Requests: {stats['total_requests']}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await registry.close_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)