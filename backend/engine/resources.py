"""Resource management system - simplified"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manages strategic resources"""

    def __init__(self):
        self.resources = {}

    def process_resources(self, world) -> List:
        """Process resource changes for the current turn"""
        # Simplified: basic oil price fluctuation
        import random
        change = random.randint(-5, 5)
        world.oil_price = max(20, min(200, world.oil_price + change))
        return []

    def get_country_resources(self, country_id: str) -> Dict:
        """Get resources for a country"""
        return self.resources.get(country_id, {})

    def reset(self):
        """Reset resource state"""
        self.resources = {}


# Global instance
resource_manager = ResourceManager()
