# ============================================================================
# FILE: src/tools/web_search.py
# ============================================================================
"""Web search tool using DuckDuckGo"""
from typing import Dict, Any
from src.tools.base import BaseTool
from src.models import ToolSchema


class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo API"""
    
    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="web_search",
            description="Search the internet for current information, news, or general knowledge. Use for factual queries, recent events, or topics requiring up-to-date information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (2-50 words recommended)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (1-10)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        )
    
    async def _execute_impl(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute DuckDuckGo search"""
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        
        response = await self.http_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Extract Abstract
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "Abstract"),
                "snippet": data.get("Abstract", ""),
                "url": data.get("AbstractURL", "")
            })
        
        # Extract Related Topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", "")[:50],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", "")
                })
        
        return {
            "query": query,
            "results": results[:max_results],
            "result_count": len(results[:max_results]),
            "sources": [{
                "name": "DuckDuckGo Search",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
            }]
        }
