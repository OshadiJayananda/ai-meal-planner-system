"""Dummy nutrition agent."""


class NutritionAgent:
    """Adds placeholder calorie estimates."""

    def run(self, meals: list) -> list:
        """Input: list of meal dicts. Output: same meals enriched with calories."""
        calories = [250, 420, 320]
        with_calories = []
        for meal, kcal in zip(meals, calories):
            meal_copy = dict(meal)
            meal_copy["calories"] = kcal
            with_calories.append(meal_copy)
        return with_calories
