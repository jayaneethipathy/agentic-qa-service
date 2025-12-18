# ============================================================================
# FILE: src/tools/weather.py
# ============================================================================
"""Weather tool (dummy implementation for demo)"""
import random
import asyncio
from typing import Dict, Any
from src.tools.base import BaseTool
from src.models import ToolSchema


class WeatherTool(BaseTool):
    """Get weather information for a location (dummy data)"""
    
    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="weather",
            description="Get current weather information including temperature, conditions, humidity, and wind speed for any city or location worldwide.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'Paris', 'New York, NY', 'Tokyo')"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature units",
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        )
    
    async def _execute_impl(self, location: str, units: str = "celsius") -> Dict[str, Any]:
        """Return realistic dummy weather data"""
        # Simulate API delay
        await asyncio.sleep(0.05)
        
        # Generate realistic data
        conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "clear", "overcast"]
        temp_c = random.randint(5, 35)
        temp_f = int(temp_c * 9/5 + 32)
        
        return {
            "location": location,
            "temperature": temp_c if units == "celsius" else temp_f,
            "units": units,
            "condition": random.choice(conditions),
            "humidity": random.randint(30, 90),
            "wind_speed_kmh": random.randint(0, 30),
            "feels_like": (temp_c - 2) if units == "celsius" else (temp_f - 4),
            "sources": [{
                "name": "Weather API (Demo)",
                "url": "internal://weather-api"
            }]
        }
