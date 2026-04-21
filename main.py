"""Dummy entry point for meal_planner_mas."""

from agents.coordinator import CoordinatorAgent
from agents.meal_agent import MealAgent
from agents.nutrition_agent import NutritionAgent
from agents.output_agent import OutputAgent
from state import PlannerState
from tools.format_tool import add_footer
from tools.input_tool import get_user_input
from tools.nutrition_tool import estimate_total_calories


def run_dummy_system() -> str:
    state = PlannerState()

    coordinator = CoordinatorAgent()
    meal_agent = MealAgent()
    nutrition_agent = NutritionAgent()
    output_agent = OutputAgent()

    state.user_input = get_user_input()
    parsed = coordinator.run(state.user_input)

    state.goal = parsed["goal"]
    state.ingredients = parsed["ingredients"]

    state.meals = meal_agent.run(parsed)
    meals_with_nutrition = nutrition_agent.run(state.meals)

    base_output = output_agent.run(meals_with_nutrition)
    total_calories = estimate_total_calories(meals_with_nutrition)

    state.final_output = add_footer(base_output, total_calories)
    return state.final_output


if __name__ == "__main__":
    print(run_dummy_system())
