# ============================================================================
# FILE: src/stream_demo.py (FIXED VERSION)
# ============================================================================
"""Streaming demo showcasing real-time response generation (BONUS)"""
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


async def stream_query(agent: AgenticQA, query: str):
    """Stream agent responses in real-time"""
    print(f"\n{'='*70}")
    print(f"Query: {query}")
    print('='*70)
    
    try:
        async for chunk in agent.query_stream(query):
            chunk_type = chunk.get("type")
            
            if chunk_type == "status":
                print(f"📍 {chunk['message']}")
            
            elif chunk_type == "planning":
                tools = chunk.get("tools", [])
                print(f"🧠 Planning: Will use {len(tools)} tool(s): {', '.join(tools)}")
            
            elif chunk_type == "tool_start":
                print(f"🔧 Executing: {chunk['tool_name']}...")
            
            elif chunk_type == "tool_result":
                latency = chunk.get("latency_ms", 0)
                status = "✅" if not chunk.get("error") else "❌"
                print(f"{status} {chunk['tool_name']} completed in {latency}ms")
            
            elif chunk_type == "synthesis":
                print(f"✍️  Synthesizing answer...")
            
            elif chunk_type == "answer":
                print(f"\n📝 Final Answer:\n{chunk['answer']}")
                print(f"\n📊 Metadata:")
                print(f"   • Latency: {chunk['latency_ms']['total']}ms")
                print(f"   • Tokens: {chunk['tokens']['prompt'] + chunk['tokens']['completion']}")
                print(f"   • Sources: {len(chunk['sources'])}")
            
            elif chunk_type == "error":
                print(f"❌ Error: {chunk['message']}")
            
            # Small delay for visual effect
            await asyncio.sleep(0.05)
    except Exception as e:
        print(f"❌ Error during streaming: {e}")


async def main():
    """Streaming demo main function"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         🌊 STREAMING DEMO - Real-time Response Generation      ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    # Initialize components
    cache = InMemoryCache()
    policy = PolicyEnforcer()
    registry = ToolRegistry()
    
    # Register tools
    print("\n📦 Initializing tools...")
    registry.register(WebSearchTool(cache=cache))
    registry.register(WeatherTool(cache=cache))
    registry.register(CalculatorTool(cache=cache))
    
    # Create agent - FIXED: use correct parameter name
    agent = AgenticQA(
        tool_registry=registry,
        policy=policy,  # Changed from policy_enforcer to policy
        max_concurrent_tools=3
    )
    
    # Demo queries
    queries = [
        "What's the weather in Tokyo?",
        "Calculate 15 * 234 + 567",
        "Search for latest AI developments"
    ]
    
    print(f"\n🎬 Running {len(queries)} demo queries...\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"Demo {i}/{len(queries)}")
        print('='*70)
        await stream_query(agent, query)
        
        if i < len(queries):
            print("\n⏸️  Pausing for 1 second...\n")
            await asyncio.sleep(1)
    
    print("\n" + "="*70)
    print("✅ Streaming demo completed successfully!")
    print("="*70)
    
    # Show cache statistics
    print("\n📊 Cache Statistics:")
    stats = cache.get_stats()
    print(f"   • Cache Hits: {stats['hits']}")
    print(f"   • Cache Misses: {stats['misses']}")
    print(f"   • Hit Rate: {stats['hit_rate']:.1%}")
    
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