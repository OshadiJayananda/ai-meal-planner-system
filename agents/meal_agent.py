"""Dummy meal generator agent."""

import logging


logger = logging.getLogger(__name__)


class MealAgent:
    """Generates placeholder meals."""

    def run(self, context: dict) -> list:
        """Input: parsed user context dict. Output: list of meal dicts with name/type."""
        logger.info("Generating placeholder meals")
        return [
            {"name": "Egg scramble", "type": "Breakfast"},
            {"name": "Grilled chicken salad", "type": "Lunch"},
            {"name": "Chicken soup", "type": "Dinner"},
        ]
