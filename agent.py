
# ============================================================================
# FILE: src/agent.py
# ============================================================================
"""Main agent with concurrency control and streaming"""
import asyncio
import json
import time
from typing import List, Dict, Any, AsyncGenerator
from src.tool_registry import ToolRegistry
from src.models import (
    AgentResponse, LatencyBreakdown, TokenUsage,
    ToolCall, ToolResult, CostBreakdown
)
from src.policy import PolicyEnforcer, PolicyViolation
from src.observability import StructuredLogger, Tracer

logger = StructuredLogger(__name__)


class AgenticQA:
    """Agentic QA system with tool orchestration"""
    
    def __init__(self, tool_registry: ToolRegistry, llm_client: None, max_concurrent_tools: int = 3):
        self.tool_registry = tool_registry
        self.llm_client = llm_client
        self.reasoning_steps = []
        self.semaphore = asyncio.Semaphore(max_concurrent_tools)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt with tool descriptions"""
        tool_descriptions = []
        for schema in self.tool_registry.get_all_schemas():
            tool_descriptions.append(
                f"- {schema.name}: {schema.description}\n"
                f"  Parameters: {json.dumps(schema.parameters, indent=2)}"
            )
        
        return f"""You are an AI assistant with access to tools. 
                Answer user questions by calling appropriate tools and synthesizing information.

                Available tools:
                {chr(10).join(tool_descriptions)}

                Process:
                1. Analyze the query to determine which tools are needed
                2. Call tools using JSON format: {{"tool": "tool_name", "args": {{...}}}}
                3. Synthesize results into a clear answer with citations

                Always cite your sources and explain your reasoning."""
    
    async def _plan_and_execute(self, query: str) -> Dict[str, Any]:
        """Plan which tools to use and execute them"""
        start_time = time.time()
        step_times = {}
        
        # Step 1: Planning
        planning_start = time.time()
        
        # Create a planning prompt
        planning_prompt = f"""Given the query: "{query}"

            Which tools should be called? Respond with JSON array of tool calls:
            [
            {{"tool": "tool_name", "args": {{"param": "value"}}}}
            ]

            Available tools: {', '.join(self.tool_registry.get_tool_names())}"""
        
        # Get tool selection from LLM (simplified - in production use function calling)
        tool_calls = await self._get_tool_calls_from_llm(query)
        step_times["planning"] = int((time.time() - planning_start) * 1000)
        
        self.reasoning_steps.append(f"Identified {len(tool_calls)} tool(s) to call")
        
        # Step 2: Execute tools in parallel
        exec_start = time.time()
        results = await self._execute_tools_parallel(tool_calls)
        step_times["tool_execution"] = int((time.time() - exec_start) * 1000)
        
        # Step 3: Synthesize answer
        synth_start = time.time()
        final_answer = await self._synthesize_answer(query, results)
        step_times["synthesis"] = int((time.time() - synth_start) * 1000)
        
        step_times["total"] = int((time.time() - start_time) * 1000)
        
        return {
            "answer": final_answer["answer"],
            "sources": final_answer["sources"],
            "step_times": step_times,
            "tokens": final_answer.get("tokens", {"prompt": 0, "completion": 0})
        }
    
    async def _get_tool_calls_from_llm(self, query: str) -> List[ToolCall]:
        """
        Get tool calls from LLM using function calling
        In production: use OpenAI function calling or Claude tool use
        """
        # Simplified heuristic-based routing (replace with actual LLM call)
        tool_calls = []
        
        query_lower = query.lower()
        
        # Simple keyword matching (replace with LLM function calling)
        if any(word in query_lower for word in ["weather", "temperature", "climate"]):
            # Extract location
            location = "Unknown"
            for word in query.split():
                if word[0].isupper() and len(word) > 2:
                    location = word
                    break
            
            tool_calls.append(ToolCall(
                tool_name="weather",
                arguments={"location": location}
            ))
        
        if any(word in query_lower for word in ["search", "find", "what is", "who is", "latest", "news"]):
            tool_calls.append(ToolCall(
                tool_name="web_search",
                arguments={"query": query, "max_results": 5}
            ))
        
        # Default to web search if no tools matched
        if not tool_calls:
            tool_calls.append(ToolCall(
                tool_name="web_search",
                arguments={"query": query, "max_results": 5}
            ))
        
        return tool_calls
    
    async def _execute_tools_parallel(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute multiple tools in parallel"""
        """Execute with concurrency limit"""
        async def execute_with_limit(call):
            async with self.semaphore:
                tool = self.tool_registry.get_tool(call.tool_name)
                if not tool:
                    return ToolResult(tool_name=call.tool_name, result=None, error="Tool not found")
                return await tool.execute(**call.arguments)
        
        tasks = [execute_with_limit(call) for call in tool_calls]
        
        # Log what you are doing for reasoning steps
        for call in tool_calls:
            self.reasoning_steps.append(f"Calling {call.tool_name} with {call.arguments}")
       


        # Execute all tools concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for r in results:
            if isinstance(r, ToolResult):
                valid_results.append(r)
            else:
                print(f"Tool execution error: {r}")
        
        return valid_results
    
    async def _synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> Dict[str, Any]:
        """Synthesize final answer from tool results"""
        # Collect all sources
        sources = []
        context_parts = []
        
        for result in tool_results:
            if result.result and not result.error:
                # Extract sources
                if "sources" in result.result:
                    sources.extend(result.result["sources"])
                
                # Build context
                if result.tool_name == "web_search":
                    for item in result.result.get("results", []):
                        context_parts.append(f"- {item.get('snippet', '')}")
                elif result.tool_name == "weather":
                    r = result.result
                    context_parts.append(
                        f"Weather in {r['location']}: {r['temperature']}°{r['units'][0].upper()}, "
                        f"{r['condition']}, humidity {r['humidity']}%"
                    )
        
        # Simple answer synthesis (in production, use LLM)
        context = "\n".join(context_parts)
        
        # For demo purposes, create a structured answer
        answer = f"Based on the available information:\n\n{context}\n\n"
        answer += f"This answer is based on {len(tool_results)} tool call(s)."
        
        self.reasoning_steps.append(f"Synthesized answer from {len(tool_results)} tool result(s)")
        
        return {
            "answer": answer,
            "sources": sources,
            "tokens": {"prompt": 500, "completion": 200}  # Simplified
        }
    
    async def query(self, question: str) -> AgentResponse:
        """Main entry point for querying the agent"""
        self.reasoning_steps = []
        
        result = await self._plan_and_execute(question)
        
        return AgentResponse(
            answer=result["answer"],
            sources=result["sources"],
            latency_ms=LatencyBreakdown(
                total=result["step_times"]["total"],
                by_step=result["step_times"]
            ),
            tokens=TokenUsage(**result["tokens"]),
            reasoning_steps=self.reasoning_steps
        )

    async def query_stream(self, question: str):
        """Stream responses incrementally"""
        yield {"type": "status", "message": "Planning tools..."}
        
        tool_calls = await self._get_tool_calls_from_llm(question)
        yield {"type": "tools", "selected": [t.tool_name for t in tool_calls]}
        
        yield {"type": "status", "message": "Executing tools..."}
        results = await self._execute_tools_parallel(tool_calls)
        
        yield {"type": "status", "message": "Synthesizing answer..."}
        final = await self._synthesize_answer(question, results)
        
        yield {"type": "answer", "data": final}

class AgentError(Exception):
    """Custom agent error with context"""
    def __init__(self, message: str, context: dict):
        self.message = message
        self.context = context
        super().__init__(message)

async def _execute_with_fallback(self, tool_call):
    """Execute with fallback strategy"""
    try:
        return await self._execute_primary(tool_call)
    except Exception as e:
        print(f"Primary execution failed: {e}, trying fallback...")
        return await self._execute_fallback(tool_call)
