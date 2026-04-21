"""Dummy coordinator agent."""


class CoordinatorAgent:
    """Coordinates the meal-planning flow."""

    def run(self, user_input: str) -> dict:
        return {
            "goal": "weight loss",
            "ingredients": ["chicken", "eggs"],
            "raw_input": user_input,
        }
