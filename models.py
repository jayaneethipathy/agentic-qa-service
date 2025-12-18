# ============================================================================
# FILE: src/models.py
# ============================================================================
"""Pydantic models for structured I/O with JSON Schema validation"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source attribution"""
    name: str = Field(..., description="Source name")
    url: str = Field(..., description="Source URL")


class LatencyBreakdown(BaseModel):
    """Detailed latency tracking"""
    total: int = Field(..., description="Total latency in ms")
    by_step: Dict[str, int] = Field(default_factory=dict, description="Per-step latency")


class TokenUsage(BaseModel):
    """Token tracking for cost management"""
    prompt: int = Field(default=0, ge=0)
    completion: int = Field(default=0, ge=0)
    
    @property
    def total(self) -> int:
        return self.prompt + self.completion
    
    @property
    def estimated_cost_usd(self) -> float:
        """Estimate cost based on GPT-4 pricing"""
        # GPT-4: $0.03/1K prompt, $0.06/1K completion
        return (self.prompt * 0.03 / 1000) + (self.completion * 0.06 / 1000)


class CostBreakdown(BaseModel):
    """Detailed cost tracking"""
    total_cost_usd: float = 0.0
    llm_cost: float = 0.0
    embedding_cost: float = 0.0
    tool_cost: float = 0.0


class AgentResponse(BaseModel):
    """Structured agent response"""
    answer: str
    sources: List[Source]
    latency_ms: LatencyBreakdown
    tokens: TokenUsage
    cost: Optional[CostBreakdown] = None
    reasoning_steps: Optional[List[str]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class ToolSchema(BaseModel):
    """Tool definition with JSON Schema"""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    def to_openai_format(self) -> Dict:
        """Convert to OpenAI function calling format"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolCall(BaseModel):
    """Tool invocation request"""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


class ToolResult(BaseModel):
    """Tool execution result"""
    tool_name: str
    result: Any
    latency_ms: int
    error: Optional[str] = None
    cached: bool = False