# ============================================================================
# FILE: src/tools/calculator.py
# ============================================================================
"""Calculator tool for mathematical operations"""
from typing import Dict, Any
from src.tools.base import BaseTool
from src.models import ToolSchema
import ast
import operator


class CalculatorTool(BaseTool):
    """Perform mathematical calculations"""
    
    # Safe operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }
    
    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="calculator",
            description="Perform mathematical calculations. Supports basic arithmetic (+, -, *, /), exponents (**), and modulo (%).",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5 + 3')"
                    }
                },
                "required": ["expression"]
            }
        )
    
    def _eval_expr(self, node):
        """Safely evaluate mathematical expression"""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type}")
            return self.OPERATORS[op_type](
                self._eval_expr(node.left),
                self._eval_expr(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -self._eval_expr(node.operand)
            elif isinstance(node.op, ast.UAdd):
                return self._eval_expr(node.operand)
        raise ValueError(f"Unsupported expression type: {type(node)}")
    
    async def _execute_impl(self, expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expression safely"""
        try:
            # Parse and evaluate
            tree = ast.parse(expression, mode='eval')
            result = self._eval_expr(tree.body)
            
            return {
                "expression": expression,
                "result": result,
                "success": True,
                "sources": [{
                    "name": "Calculator",
                    "url": "internal://calculator"
                }]
            }
        except Exception as e:
            return {
                "expression": expression,
                "result": None,
                "success": False,
                "error": str(e),
                "sources": [{
                    "name": "Calculator",
                    "url": "internal://calculator"
                }]
            }