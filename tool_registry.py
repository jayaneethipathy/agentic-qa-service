# ============================================================================
# FILE: src/tool_registry.py
# ============================================================================
"""Tool registry for dynamic tool management"""
from typing import Dict, List, Optional
from src.tools.base import BaseTool
from src.models import ToolSchema
from src.observability import StructuredLogger

logger = StructuredLogger(__name__)


class ToolRegistry:
    """Centralized tool management"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """Register a tool"""
        schema = tool.get_schema()
        self._tools[schema.name] = tool
        logger.info("tool_registered", tool_name=schema.name)
    
    def unregister(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info("tool_unregistered", tool_name=tool_name)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def get_all_schemas(self) -> List[ToolSchema]:
        """Get all tool schemas for LLM"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names"""
        return list(self._tools.keys())
    
    def list_tools(self) -> List[Dict[str, str]]:
        """List all tools with descriptions"""
        return [
            {
                "name": schema.name,
                "description": schema.description
            }
            for schema in self.get_all_schemas()
        ]
    
    async def close_all(self):
        """Close all tools and cleanup"""
        for tool_name, tool in self._tools.items():
            try:
                await tool.close()
                logger.info("tool_closed", tool_name=tool_name)
            except Exception as e:
                logger.error("tool_close_failed", 
                           tool_name=tool_name,
                           error=str(e))