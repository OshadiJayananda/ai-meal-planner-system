"""Dummy shared state."""


class PlannerState:
    def __init__(self) -> None:
        self.user_input = ""
        self.parsed_request = {}
        self.goal = ""
        self.ingredients = []
        self.avoid_ingredients = []
        self.target_calories = None
        self.diet_type = "none"
        self.steps = []
        self.executed_steps = []
        self.meals = []
        self.nutrition_result = {}
        # Aggregated daily nutrition totals produced by NutritionAgent
        self.daily_totals: dict[str, float] = {}
        self.final_output = ""
        self.trace_events = []
        self.errors = []
