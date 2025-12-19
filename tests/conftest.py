"""Pytest fixtures and configuration"""
import pytest
import asyncio
from src.cache import InMemoryCache
from src.tool_registry import ToolRegistry
from src.tools.web_search import WebSearchTool
from src.tools.weather import WeatherTool
from src.tools.calculator import CalculatorTool
from src.policy import PolicyEnforcer
from src.agent import AgenticQA


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def cache():
    """Create cache instance"""
    cache = InMemoryCache()
    yield cache
    await cache.clear()


@pytest.fixture
async def tool_registry(cache):
    """Create tool registry with all tools"""
    registry = ToolRegistry()
    registry.register(WebSearchTool(cache=cache))
    registry.register(WeatherTool(cache=cache))
    registry.register(CalculatorTool(cache=cache))
    yield registry
    await registry.close_all()


@pytest.fixture
def policy_enforcer():
    """Create policy enforcer"""
    return PolicyEnforcer()


@pytest.fixture
async def agent(tool_registry, policy_enforcer):
    """Create agent instance - FIXED: using 'policy' instead of 'policy_enforcer'"""
    return AgenticQA(
        tool_registry=tool_registry,
        policy=policy_enforcer,  # Changed from policy_enforcer
        max_concurrent_tools=3
    )


@pytest.fixture
def sample_query():
    """Sample query for testing"""
    return "What's the weather in Paris?"


@pytest.fixture
def sample_tool_result():
    """Sample tool result"""
    return {
        "location": "Paris",
        "temperature": 18,
        "condition": "sunny",
        "sources": [{"name": "Weather API", "url": "internal"}]
    }