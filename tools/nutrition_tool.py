"""Dummy nutrition tool."""


def estimate_total_calories(meals_with_nutrition: list) -> int:
    return sum(item.get("calories", 0) for item in meals_with_nutrition)
