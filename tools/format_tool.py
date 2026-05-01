"""Formatting tool for output agent."""

from typing import Dict, List, Optional


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

# ============================================
# NEW TOOL 1: VALIDATE MEALS
# ============================================
def validate_meal_data(meals: List[Dict]) -> List[Dict]:
    """
    Ensure meals have required fields and valid types.
    Removes invalid meals.
    """
    valid_meals = []

    for meal in meals:
        if not meal.get("name") or not meal.get("description"):
            continue  # skip bad data

        if meal.get("type") not in ["Breakfast", "Lunch", "Dinner", "Snack"]:
            meal["type"] = "Meal"

        valid_meals.append(meal)

    return valid_meals


# ============================================
# NEW TOOL 2: NORMALIZE DATA
# ============================================
def normalize_meal_fields(meals: List[Dict]) -> List[Dict]:
    """
    Clean and standardize meal fields.
    """
    for meal in meals:
        meal["name"] = meal.get("name", "").strip()
        meal["description"] = meal.get("description", "").strip()

        if "portion_guidance" in meal and meal["portion_guidance"]:
            if len(meal["portion_guidance"]) > 200:
                meal["portion_guidance"] = meal["portion_guidance"][:200] + "..."

    return meals


# ============================================
# NEW TOOL 3: CALORIE ALIGNMENT CHECK
# ============================================
def check_calorie_alignment(total: int, target: int) -> str:
    """
    Compare actual calories with target and return a human-readable message.
    """
    if target <= 0:
        return "No target calorie specified."

    diff = total - target

    if abs(diff) < 100:
        return "Calorie intake is well aligned with the target."
    elif diff < 0:
        return f"Meal plan is too low by {abs(diff)} kcal."
    else:
        return f"Meal plan exceeds target by {diff} kcal."