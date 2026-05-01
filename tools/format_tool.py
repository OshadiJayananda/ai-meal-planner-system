"""Formatting tool for output agent."""

from typing import Optional


def add_footer(report: str, total_calories: Optional[int]) -> str:
    """
    Append calorie summary to the report if available.

    Args:
        report (str): Generated meal plan report
        total_calories (Optional[int]): Total calories (can be None)

    Returns:
        str: Final formatted report
    """

    if total_calories is None or total_calories == 0:
        return report  # ✅ Do not add misleading info

    return f"{report}\n\nTotal Estimated Calories: {total_calories} kcal"