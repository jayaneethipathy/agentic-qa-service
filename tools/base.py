# ============================================================================
# FILE: src/tools/base.py
# ============================================================================
"""Base tool interface with validation"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from jsonschema import validate, ValidationError
import json
from src.models import ToolSchema, ToolResult
from src.observability import StructuredLogger

logger = StructuredLogger(__name__)


class BaseTool(ABC):
    """Base class for all tools with retry and validation"""
    
    def __init__(self, cache: Optional[Any] = None):
        self.cache = cache
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """Return tool schema for LLM"""
        pass
    
    @abstractmethod
    async def _execute_impl(self, **kwargs) -> Dict[str, Any]:
        """Actual tool execution logic"""
        pass
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Define expected output schema for validation"""
        return {
            "type": "object",
            "required": ["sources"],
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "url": {"type": "string"}
                        }
                    }
                }
            }
        }
    
    def validate_output(self, result: Dict[str, Any]) -> bool:
        """Validate tool output against schema"""
        try:
            schema = self.get_output_schema()
            validate(instance=result, schema=schema)
            return True
        except ValidationError as e:
            logger.error("validation_failed", 
                        tool=self.get_schema().name,
                        error=str(e))
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def execute(self, **kwargs) -> ToolResult:
        """Execute tool with caching, retries, and validation"""
        start_time = time.time()
        tool_name = self.get_schema().name
        
        # Check cache
        cached = False
        if self.cache:
            cache_key = f"{tool_name}:{json.dumps(kwargs, sort_keys=True)}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.info("cache_hit", tool=tool_name)
                return ToolResult(
                    tool_name=tool_name,
                    result=cached_result,
                    latency_ms=int((time.time() - start_time) * 1000),
                    cached=True
                )
        
        try:
            # Execute tool
            result = await self._execute_impl(**kwargs)
            
            # Validate output
            if not self.validate_output(result):
                logger.warning("output_validation_failed", tool=tool_name)
            
            latency = int((time.time() - start_time) * 1000)
            
            # Cache result
            if self.cache and not cached:
                await self.cache.set(cache_key, result, ttl=300)
            
            logger.info("tool_executed", 
                       tool=tool_name,
                       latency_ms=latency,
                       cached=cached)
            
            return ToolResult(
                tool_name=tool_name,
                result=result,
                latency_ms=latency,
                cached=cached
            )
            
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error("tool_execution_failed",
                        tool=tool_name,
                        error=str(e),
                        latency_ms=latency)
            
            return ToolResult(
                tool_name=tool_name,
                result=None,
                latency_ms=latency,
                error=str(e)
            )


    def validate_tool_output(self, result: dict):
        """Validate tool output against schema"""
        schema = {
            "type": "object",
            "required": ["sources"],
            "properties": {
                "sources": {"type": "array"}
            }
        }
        try:
            validate(instance=result, schema=schema)
            return True
        except ValidationError as e:
            print(f"Validation error: {e}")
            return False




    async def close(self):
        """Cleanup resources"""
        await self.http_client.aclose()