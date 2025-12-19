# ============================================================================
# FILE: src/agent.py (CORRECTED VERSION - Replace your current file)
# ============================================================================
"""Main agent with concurrency control and streaming"""
import asyncio
import json
import time
from typing import List, Dict, Any, AsyncGenerator, Optional
from src.tool_registry import ToolRegistry
from src.models import (
    AgentResponse, LatencyBreakdown, TokenUsage, Source,
    ToolCall, ToolResult, CostBreakdown
)
from src.policy import PolicyEnforcer, PolicyViolation
from src.observability import StructuredLogger, Tracer

logger = StructuredLogger(__name__)


class AgenticQA:
    """Agentic QA system with tool orchestration"""
    
    def __init__(
        self, 
        tool_registry: ToolRegistry, 
        policy: Optional[PolicyEnforcer] = None,
        max_concurrent_tools: int = 3
    ):
        self.tool_registry = tool_registry
        self.policy = policy or PolicyEnforcer()  # Create default if not provided
        self.reasoning_steps = []
        self.semaphore = asyncio.Semaphore(max_concurrent_tools)
        self.tracer = Tracer()
    
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
    
    async def _get_tool_calls_from_llm(self, query: str) -> List[ToolCall]:
        """
        Get tool calls from LLM using function calling
        In production: use OpenAI function calling or Claude tool use
        """
        tool_calls = []
        query_lower = query.lower()
        
        # Math detection
        math_keywords = ["calculate", "compute", "math", "sum", "multiply", "divide"]
        has_operators = any(op in query for op in ["+", "-", "*", "/", "**", "%"])
        
        if any(kw in query_lower for kw in math_keywords) or has_operators:
            # Extract expression
            import re
            expr_match = re.search(r'[\d\s+\-*/()%.]+', query)
            if expr_match:
                expression = expr_match.group().strip()
                if any(op in expression for op in ["+", "-", "*", "/", "**", "%"]):
                    tool_calls.append(ToolCall(
                        tool_name="calculator",
                        arguments={"expression": expression}
                    ))
        
        # Weather detection
        if any(word in query_lower for word in ["weather", "temperature", "climate", "forecast"]):
            # Extract location
            location = "Unknown"
            words = query.split()
            for i, word in enumerate(words):
                if i > 0 and word and word[0].isupper() and len(word) > 2:
                    if word.lower() not in ["what", "the", "is", "in", "at"]:
                        location = word
                        # Check for multi-word location
                        if i + 1 < len(words) and words[i+1][0].isupper():
                            location = f"{word} {words[i+1]}"
                        break
            
            tool_calls.append(ToolCall(
                tool_name="weather",
                arguments={"location": location}
            ))
        
        # Web search detection
        search_keywords = ["search", "find", "what is", "who is", "latest", "news", "information"]
        should_search = any(kw in query_lower for kw in search_keywords)
        
        # Default to web search if no tools matched
        if not tool_calls or should_search:
            if not any(tc.tool_name == "web_search" for tc in tool_calls):
                tool_calls.append(ToolCall(
                    tool_name="web_search",
                    arguments={"query": query, "max_results": 5}
                ))
        
        return tool_calls
    
    async def _execute_tool_with_limit(self, tool_call: ToolCall, query: str) -> ToolResult:
        """Execute tool with concurrency limit and policy check"""
        async with self.semaphore:
            # Policy validation
            try:
                self.policy.validate_tool_call(
                    tool_call.tool_name,
                    tool_call.arguments,
                    query
                )
            except PolicyViolation as e:
                logger.error("policy_violation", tool=tool_call.tool_name, error=str(e))
                return ToolResult(
                    tool_name=tool_call.tool_name,
                    result=None,
                    latency_ms=0,
                    error=f"Policy violation: {e}"
                )
            
            # Get tool
            tool = self.tool_registry.get_tool(tool_call.tool_name)
            if not tool:
                logger.error("tool_not_found", tool_name=tool_call.tool_name)
                return ToolResult(
                    tool_name=tool_call.tool_name,
                    result=None,
                    latency_ms=0,
                    error=f"Tool '{tool_call.tool_name}' not found"
                )
            
            # Execute
            return await tool.execute(**tool_call.arguments)
    
    async def _execute_tools_parallel(self, tool_calls: List[ToolCall], query: str = "") -> List[ToolResult]:
        """Execute multiple tools in parallel with concurrency control"""
        tasks = [
            self._execute_tool_with_limit(call, query)
            for call in tool_calls
        ]
        
        # Log reasoning steps
        for call in tool_calls:
            self.reasoning_steps.append(f"Calling {call.tool_name} with {call.arguments}")
        
        # Execute all tools concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for r in results:
            if isinstance(r, ToolResult):
                valid_results.append(r)
            elif isinstance(r, Exception):
                logger.error("tool_execution_exception", error=str(r))
        
        return valid_results
    
    async def _synthesize_answer(self, query: str, tool_results: List[ToolResult]) -> Dict[str, Any]:
        """Synthesize final answer from tool results"""
        sources = []
        context_parts = []
        
        for result in tool_results:
            if result.error:
                context_parts.append(f"{result.tool_name} failed: {result.error}")
                continue
            
            if not result.result:
                continue
            
            # Extract sources
            if "sources" in result.result:
                sources.extend(result.result["sources"])
            
            # Build context based on tool type
            if result.tool_name == "web_search":
                search_results = result.result.get("results", [])
                if search_results:
                    context_parts.append(f"\n🔍 Web Search Results:")
                    for idx, item in enumerate(search_results[:3], 1):
                        snippet = item.get("snippet", "")[:200]
                        context_parts.append(f"   {idx}. {snippet}")
            
            elif result.tool_name == "weather":
                r = result.result
                context_parts.append(
                    f"\n🌤️  Weather in {r['location']}: {r['temperature']}°{r['units'][0].upper()}, "
                    f"{r['condition']}, humidity {r['humidity']}%"
                )
            
            elif result.tool_name == "calculator":
                r = result.result
                if r.get("success"):
                    context_parts.append(
                        f"\n🔢 Calculation: {r['expression']} = {r['result']}"
                    )
                else:
                    context_parts.append(f"\nCalculation failed: {r.get('error', 'Unknown error')}")
        
        # Build final answer
        context = "\n".join(context_parts)
        answer = f"Based on the available information:{context}\n\n"
        answer += f"This answer is based on {len(tool_results)} tool call(s)."
        
        self.reasoning_steps.append(f"Synthesized answer from {len(tool_results)} tool result(s)")
        
        return {
            "answer": answer,
            "sources": sources,
            "tokens": {"prompt": 500, "completion": 200}
        }
    
    async def query(self, question: str) -> AgentResponse:
        """Main entry point for querying the agent (non-streaming)"""
        self.reasoning_steps = []
        self.tracer.clear()
        start_time = time.time()
        step_times = {}
        
        # Step 1: Planning
        planning_start = time.time()
        tool_calls = await self._get_tool_calls_from_llm(question)
        step_times["planning"] = int((time.time() - planning_start) * 1000)
        self.reasoning_steps.append(f"Identified {len(tool_calls)} tool(s) to call")
        
        # Step 2: Execute tools
        exec_start = time.time()
        results = await self._execute_tools_parallel(tool_calls, question)
        step_times["tool_execution"] = int((time.time() - exec_start) * 1000)
        
        # Step 3: Synthesize
        synth_start = time.time()
        final_answer = await self._synthesize_answer(question, results)
        step_times["synthesis"] = int((time.time() - synth_start) * 1000)
        
        step_times["total"] = max(1, int((time.time() - start_time) * 1000))
        
        # Calculate cost
        cost = CostBreakdown(
            total_cost_usd=final_answer["tokens"]["prompt"] * 0.03 / 1000 + 
                          final_answer["tokens"]["completion"] * 0.06 / 1000,
            llm_cost=final_answer["tokens"]["prompt"] * 0.03 / 1000 + 
                    final_answer["tokens"]["completion"] * 0.06 / 1000,
            tool_cost=0.001 * len(results)
        )
        
        return AgentResponse(
            answer=final_answer["answer"],
            sources=[Source(**s) for s in final_answer["sources"]],
            latency_ms=LatencyBreakdown(total=step_times["total"], by_step=step_times),
            tokens=TokenUsage(**final_answer["tokens"]),
            cost=cost,
            reasoning_steps=self.reasoning_steps
        )
    
    async def query_stream(self, question: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream agent responses in real-time (BONUS FEATURE)
        Yields chunks as the agent progresses through steps
        """
        self.reasoning_steps = []
        self.tracer.clear()
        start_time = time.time()
        step_times = {}
        
        try:
            # Status: Starting
            yield {"type": "status", "message": "Starting query processing..."}
            
            # Step 1: Planning
            yield {"type": "status", "message": "Planning tool selection..."}
            planning_start = time.time()
            tool_calls = await self._get_tool_calls_from_llm(question)
            step_times["planning"] = int((time.time() - planning_start) * 1000)
            
            yield {
                "type": "planning",
                "tools": [call.tool_name for call in tool_calls],
                "count": len(tool_calls)
            }
            
            self.reasoning_steps.append(f"Identified {len(tool_calls)} tool(s) to call")
            
            # Step 2: Execute tools
            yield {"type": "status", "message": "Executing tools..."}
            exec_start = time.time()
            
            # Execute tools and stream results as they complete
            results = []
            for call in tool_calls:
                yield {
                    "type": "tool_start",
                    "tool_name": call.tool_name,
                    "arguments": call.arguments
                }
                
                result = await self._execute_tool_with_limit(call, question)
                results.append(result)
                
                yield {
                    "type": "tool_result",
                    "tool_name": result.tool_name,
                    "latency_ms": result.latency_ms,
                    "error": result.error,
                    "cached": result.cached
                }
                
                self.reasoning_steps.append(f"Calling {call.tool_name} with {call.arguments}")
            
            step_times["tool_execution"] = int((time.time() - exec_start) * 1000)
            
            # Step 3: Synthesize
            yield {"type": "synthesis", "message": "Synthesizing final answer..."}
            synth_start = time.time()
            final_answer = await self._synthesize_answer(question, results)
            step_times["synthesis"] = int((time.time() - synth_start) * 1000)
            
            step_times["total"] = max(1, int((time.time() - start_time) * 1000))
            
            # Calculate cost
            cost = {
                "total_cost_usd": final_answer["tokens"]["prompt"] * 0.03 / 1000 + 
                                 final_answer["tokens"]["completion"] * 0.06 / 1000,
                "llm_cost": final_answer["tokens"]["prompt"] * 0.03 / 1000 + 
                           final_answer["tokens"]["completion"] * 0.06 / 1000,
                "tool_cost": 0.001 * len(results)
            }
            
            # Final answer
            yield {
                "type": "answer",
                "answer": final_answer["answer"],
                "sources": final_answer["sources"],
                "latency_ms": step_times,
                "tokens": final_answer["tokens"],
                "cost": cost,
                "reasoning_steps": self.reasoning_steps
            }
            
        except Exception as e:
            logger.error("streaming_error", error=str(e))
            yield {
                "type": "error",
                "message": str(e),
                "timestamp": time.time()
            }


class AgentError(Exception):
    """Custom agent error with context"""
    def __init__(self, message: str, context: dict):
        self.message = message
        self.context = context
        super().__init__(message)