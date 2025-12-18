# ============================================================================
# FILE: src/observability.py
# ============================================================================
"""Observability and monitoring utilities"""
import json
import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class StructuredLogger:
    """JSON structured logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log(self, level: str, event: str, **kwargs):
        """Log structured event"""
        log_entry = {
            "timestamp": time.time(),
            "event": event,
            **kwargs
        }
        getattr(self.logger, level)(json.dumps(log_entry))
    
    def info(self, event: str, **kwargs):
        self.log("info", event, **kwargs)
    
    def error(self, event: str, **kwargs):
        self.log("error", event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        self.log("warning", event, **kwargs)


class Tracer:
    """Distributed tracing utility"""
    
    def __init__(self):
        self.spans: list = []
    
    @contextmanager
    def span(self, operation: str, **attributes):
        """Create a trace span"""
        span_id = f"{operation}_{len(self.spans)}"
        start = time.time()
        
        try:
            yield span_id
        finally:
            duration = int((time.time() - start) * 1000)
            self.spans.append({
                "span_id": span_id,
                "operation": operation,
                "duration_ms": duration,
                "attributes": attributes
            })
    
    def get_trace(self) -> list:
        """Get all spans in trace"""
        return self.spans
    
    def clear(self):
        """Clear trace"""
        self.spans.clear()

class Logger:
    @contextmanager
    def trace_operation(self, operation: str):
        start = time.time()
        try:
            yield
        finally:
            duration = int((time.time() - start) * 1000)
            print(json.dumps({
                "operation": operation,
                "duration_ms": duration,
                "timestamp": time.time()
            }))