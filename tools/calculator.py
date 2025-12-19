# ============================================================================
# FILE: src/tools/calculator.py
# ============================================================================
# ============================================================================
# FILE: src/tools/calculator.py
# ============================================================================
"""Calculator tool for mathematical operations"""
from typing import Dict, Any
import ast
import operator
from src.tools.base import BaseTool
from src.models import ToolSchema


class CalculatorTool(BaseTool):
    """Perform mathematical calculations safely"""
    
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
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5 + 3', '2 ** 8')"
                    }
                },
                "required": ["expression"]
            }
        )
    
    def _eval_expr(self, node):
        """Safely evaluate mathematical expression using AST"""
        if isinstance(node, ast.Num):  # Python 3.7 compatibility
            return node.n
        elif isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return self.OPERATORS[op_type](
                self._eval_expr(node.left),
                self._eval_expr(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -self._eval_expr(node.operand)
            elif isinstance(node.op, ast.UAdd):
                return self._eval_expr(node.operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    async def _execute_impl(self, expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expression safely"""
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Parse and evaluate using AST (safe - no code execution)
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
        except SyntaxError as e:
            return {
                "expression": expression,
                "result": None,
                "success": False,
                "error": f"Syntax error: {str(e)}",
                "sources": [{
                    "name": "Calculator",
                    "url": "internal://calculator"
                }]
            }
        except (ValueError, ZeroDivisionError) as e:
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
        except Exception as e:
            return {
                "expression": expression,
                "result": None,
                "success": False,
                "error": f"Calculation error: {str(e)}",
                "sources": [{
                    "name": "Calculator",
                    "url": "internal://calculator"
                }]
            }