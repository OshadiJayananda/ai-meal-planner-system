"""Dummy entry point for meal_planner_mas."""

import logging

from agents.coordinator import CoordinatorAgent
from agents.meal_agent import MealAgent
from agents.nutrition_agent import NutritionAgent
from agents.output_agent import OutputAgent
from state import PlannerState
from tools.format_tool import add_footer
from tools.input_tool import get_user_input
from tools.nutrition_tool import estimate_total_calories


logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_dummy_system() -> str:
    setup_logging()

    state = PlannerState()

    coordinator = CoordinatorAgent()
    meal_agent = MealAgent()
    nutrition_agent = NutritionAgent()
    output_agent = OutputAgent()

    state.user_input = get_user_input()
    parsed = coordinator.run(state.user_input)

    state.goal = parsed["goal"]
    state.ingredients = parsed["ingredients"]
    state.avoid_ingredients = parsed["avoid_ingredients"]
    state.target_calories = parsed["target_calories"]
    state.diet_type = parsed["diet_type"]
    steps = parsed["steps"]
    state.steps = steps

    logger.info("> Meal Agent: Suggest meals...")
    state.meals = meal_agent.run(parsed)
    
    logger.info("> Nutrition Agent: Calculating calories...")
    meals_with_nutrition = nutrition_agent.run(state.meals)

    logger.info("> Output Agent: Formatting final plan...")
    base_output = output_agent.run(meals_with_nutrition)
    total_calories = estimate_total_calories(meals_with_nutrition)

    state.final_output = add_footer(base_output, total_calories)
    logger.info("> Meal planning pipeline completed successfully.")
    print("\nFinal Plan:")
    return state.final_output


if __name__ == "__main__":
    print(run_dummy_system())
