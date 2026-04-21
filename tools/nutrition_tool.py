"""Dummy nutrition tool."""

import logging


logger = logging.getLogger(__name__)


def estimate_total_calories(meals_with_nutrition: list) -> int:
    total = sum(item.get("calories", 0) for item in meals_with_nutrition)
    logger.info("Estimated total calories: %s", total)
    return total
