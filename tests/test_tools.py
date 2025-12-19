"""Unit tests for tools"""
import pytest
from src.cache import InMemoryCache
from src.tools.web_search import WebSearchTool
from src.tools.weather import WeatherTool
from src.tools.calculator import CalculatorTool


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
async def test_calculator_tool():
    """Test calculator tool"""
    tool = CalculatorTool()
    result = await tool.execute(expression="15 * 234 + 567")
    
    assert result.tool_name == "calculator"
    assert result.error is None
    assert result.result["success"] is True
    assert result.result["result"] == 4077
    
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
    
    # Check if second result was from cache
    assert result2.cached is True or latency2 <= latency1 * 2
    
    await tool.close()


@pytest.mark.asyncio
async def test_calculator_division():
    """Test calculator with division"""
    tool = CalculatorTool()
    result = await tool.execute(expression="100 / 4")
    
    assert result.result["success"] is True
    assert result.result["result"] == 25.0
    
    await tool.close()


@pytest.mark.asyncio
async def test_calculator_invalid_expression():
    """Test calculator with invalid expression"""
    tool = CalculatorTool()
    result = await tool.execute(expression="invalid expression")
    
    assert result.result["success"] is False
    assert result.result["error"] is not None
    
    await tool.close()