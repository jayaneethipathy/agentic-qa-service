"""Integration tests for agent"""
import pytest
from src.cache import InMemoryCache
from src.tool_registry import ToolRegistry
from src.tools.web_search import WebSearchTool
from src.tools.weather import WeatherTool
from src.agent import AgenticQA


@pytest.mark.asyncio
async def test_agent_query():
    """Test full agent query flow"""
    cache = InMemoryCache()
    registry = ToolRegistry()
    registry.register(WebSearchTool(cache=cache))
    registry.register(WeatherTool(cache=cache))
    
    agent = AgenticQA(tool_registry=registry,llm_client=None)
    
    response = await agent.query("What's the weather in Tokyo?")
    
    assert response.answer is not None
    assert len(response.sources) > 0
    assert response.latency_ms.total > 0
    assert len(response.reasoning_steps) > 0
    
    await registry.close_all()


@pytest.mark.asyncio
async def test_agent_multi_tool():
    """Test agent with multiple tools"""
    cache = InMemoryCache()
    registry = ToolRegistry()
    registry.register(WebSearchTool(cache=cache))
    registry.register(WeatherTool(cache=cache))
    
    agent = AgenticQA(tool_registry=registry,llm_client=None)
    
    response = await agent.query("Weather in Paris and search for French news")
    
    # assert "weather" in response.reasoning_steps[0].lower() or "web_search" in response.reasoning_steps[0].lower()
    steps_joined = "".join(response.reasoning_steps).lower()
    assert "weather" in steps_joined
    assert "web_search" in steps_joined
    assert response.latency_ms.total > 0
    
    await registry.close_all()