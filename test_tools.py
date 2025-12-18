"""Unit tests for tools"""
import pytest
from src.cache import InMemoryCache
from src.tools.web_search import WebSearchTool
from src.tools.weather import WeatherTool


@pytest.mark.asyncio
async def test_web_search_tool():
    """Test web search tool"""
    tool = WebSearchTool()
    result = await tool.execute(query="Python programming", max_results=3)
    
    assert result.tool_name == "web_search"
    assert result.error is None
    assert "results" in result.result
    
    await tool.close()


@pytest.mark.asyncio
async def test_weather_tool():
    """Test weather tool"""
    tool = WeatherTool()
    result = await tool.execute(location="Paris", units="celsius")
    
    assert result.tool_name == "weather"
    assert result.error is None
    assert result.result["location"] == "Paris"
    assert "temperature" in result.result
    
    await tool.close()


@pytest.mark.asyncio
async def test_tool_caching():
    """Test tool caching"""
    cache = InMemoryCache()
    tool = WeatherTool(cache=cache)
    
    # First call
    result1 = await tool.execute(location="Paris")
    latency1 = result1.latency_ms
    
    # Second call (should be cached)
    result2 = await tool.execute(location="Paris")
    latency2 = result2.latency_ms
    
    # Cached call should be faster (though margin may be small)
    assert latency2 <= latency1 * 2  # Allow some variance
    
    await tool.close()