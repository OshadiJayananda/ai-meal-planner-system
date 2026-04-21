"""Dummy shared state."""


class PlannerState:
    def __init__(self) -> None:
        self.user_input = ""
        self.goal = ""
        self.ingredients = []
        self.meals = []
        self.final_output = ""
