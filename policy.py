# ============================================================================
# FILE: src/policy.py
# ============================================================================
"""Policy layer for security and compliance"""
from typing import List, Optional
from urllib.parse import urlparse
import re


class PolicyViolation(Exception):
    """Policy violation exception"""
    pass


class PolicyEnforcer:
    """Enforce usage policies and security rules"""
    
    def __init__(self):
        # Domain blocklist
        self.blocked_domains = {
            "malicious.com",
            "spam.site",
            "phishing.net"
        }
        
        # Tool allowlist
        self.allowed_tools = {
            "web_search",
            "weather",
            "calculator"
        }
        
        # Query content filters (simple patterns)
        self.blocked_patterns = [
            r"hack\s+into",
            r"ddos\s+attack",
            r"exploit\s+vulnerability"
        ]
    
    def check_tool_allowed(self, tool_name: str) -> bool:
        """Check if tool usage is allowed"""
        if tool_name not in self.allowed_tools:
            raise PolicyViolation(f"Tool '{tool_name}' is not in allowlist")
        return True
    
    def check_url_allowed(self, url: str) -> bool:
        """Check if URL domain is allowed"""
        try:
            domain = urlparse(url).netloc
            if domain in self.blocked_domains:
                raise PolicyViolation(f"Domain '{domain}' is blocked")
            return True
        except Exception as e:
            raise PolicyViolation(f"Invalid URL: {e}")
    
    def check_query_content(self, query: str) -> bool:
        """Check query content against patterns"""
        query_lower = query.lower()
        for pattern in self.blocked_patterns:
            if re.search(pattern, query_lower):
                raise PolicyViolation(f"Query contains blocked content: {pattern}")
        return True
    
    def validate_tool_call(self, tool_name: str, arguments: dict, query: str) -> bool:
        """Comprehensive validation of tool call"""
        self.check_query_content(query)
        self.check_tool_allowed(tool_name)
        
        # Check URLs in arguments
        if "url" in arguments:
            self.check_url_allowed(arguments["url"])
        
        return True