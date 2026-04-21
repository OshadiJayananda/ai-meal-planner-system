"""Dummy shared state."""


class PlannerState:
    def __init__(self) -> None:
        self.user_input = ""
        self.goal = ""
        self.ingredients = []
        self.avoid_ingredients = []
        self.target_calories = None
        self.diet_type = "none"
        self.steps = []
        self.meals = []
        self.final_output = ""
