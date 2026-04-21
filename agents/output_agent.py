"""Dummy output formatter agent."""


class OutputAgent:
    """Formats placeholder output."""

    def run(self, meals_with_nutrition: list) -> str:
        """Input: list of meal dicts with calories. Output: formatted meal plan string."""
        lines = []
        for meal in meals_with_nutrition:
            lines.append(f"{meal['type']}: {meal['name']} ({meal['calories']} kcal)")
        return "\n".join(lines)
