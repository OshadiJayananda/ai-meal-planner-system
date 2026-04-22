"""Main entry point for Meal Planner MAS - Nutrition Agent Integration"""

import logging
from typing import Any, Callable

from agents.coordinator import CoordinatorAgent
from agents.meal_agent import MealAgent
from agents.nutrition_agent import NutritionAgent
from agents.output_agent import OutputAgent
from state import PlannerState
import state
from tools.format_tool import add_footer
from tools.input_tool import get_user_input
from tools.nutrition_tool import estimate_total_calories
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


logger = logging.getLogger(__name__)
DEFAULT_WORKFLOW_STEPS = ["meal_generation", "nutrition_analysis", "format_output"]


def _record_trace(state: PlannerState, event: str, details: dict[str, Any] | None = None) -> None:
    """Append a lightweight structured trace event to shared state."""
    payload = {"event": event}
    if details:
        payload["details"] = details
    state.trace_events.append(payload)


def setup_logging() -> None:
    """Setup logging configuration for observability."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("meal_planner.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_meal_planner_system() -> str:
    """
    Run the complete Multi-Agent Meal Planner System.
    
    Workflow:
    1. Coordinator - Parses user input into structured data
    2. Meal Agent - Generates meal suggestions
    3. Nutrition Agent - YOUR AGENT - Calculates nutrition for each meal
    4. Output Agent - Formats the final output
    """
    setup_logging()
    logger.info("=" * 60)
    logger.info("Starting Multi-Agent Meal Planner System")
    logger.info("=" * 60)

    # Initialize state
    state = PlannerState()

    # Initialize agents
    coordinator = CoordinatorAgent()
    meal_agent = MealAgent()
    nutrition_agent = NutritionAgent()  # YOUR agent with custom tool
    output_agent = OutputAgent()

    # ============================================
    # STEP 1: Get user input and parse with Coordinator
    # ============================================
    logger.info("📝 STEP 1: Getting user input...")
    state.user_input, age, weight = get_user_input()

    state.age = int(age) if age else 0
    state.current_weight = int(weight) if weight else 0

    logger.info(f"✓ User input: {state.user_input}")
    logger.info(f"✓ Age: {state.age}")
    logger.info(f"✓ Weight: {state.current_weight}")

    _record_trace(state, "coordinator.start", {"user_input": state.user_input})
    parsed = coordinator.run(state.user_input)

    state.parsed_request = parsed
    state.goal = parsed.get("goal", "")
    state.ingredients = parsed.get("ingredients", [])
    state.avoid_ingredients = parsed.get("avoid_ingredients", [])
    state.target_calories = parsed.get("target_calories", 0)
    state.diet_type = parsed.get("diet_type", "none")
    state.steps = parsed.get("steps", []) or DEFAULT_WORKFLOW_STEPS.copy()

    _record_trace(
        state,
        "coordinator.complete",
        {
            "goal": state.goal,
            "diet_type": state.diet_type,
            "target_calories": state.target_calories,
            "age": state.age,
            "current_weight": state.current_weight,
            "steps": state.steps,
        },
    )

    logger.info(f"✓ Goal: {state.goal}")
    logger.info(f"✓ Ingredients: {state.ingredients}")
    logger.info(f"✓ Steps selected by coordinator: {state.steps}")

    def execute_meal_generation() -> None:
        logger.info("🍳 STEP: meal_generation started")
        _record_trace(state, "meal_generation.start", {"goal": state.goal, "ingredients": state.ingredients})

        state.meals = meal_agent.run(state.parsed_request, state.age, state.current_weight)

        # Non-trivial branch: enforce vegetarian constraint before downstream analysis.
        if state.diet_type == "vegetarian":
            non_veg_keywords = ("chicken", "beef", "fish", "salmon", "pork", "meat")
            filtered_meals = [
                meal for meal in state.meals
                if all(keyword not in meal.get("name", "").lower() for keyword in non_veg_keywords)
            ]
            if filtered_meals:
                state.meals = filtered_meals
                logger.info("✓ Applied vegetarian filter to generated meals")
                _record_trace(state, "meal_generation.branch.vegetarian_filter", {"remaining_meals": len(state.meals)})
            else:
                logger.warning("Vegetarian filter removed all meals; keeping original meals as fallback")
                _record_trace(state, "meal_generation.branch.vegetarian_filter_fallback", {"fallback": True})

        logger.info(f"✓ meal_generation completed with {len(state.meals)} meals")
        _record_trace(state, "meal_generation.complete", {"meal_count": len(state.meals)})

    def execute_nutrition_analysis() -> None:
        logger.info("🧮 STEP: nutrition_analysis started")
        _record_trace(state, "nutrition_analysis.start", {"meal_count": len(state.meals)})

        state.nutrition_result = nutrition_agent.run(state.meals)
        state.meals = state.nutrition_result["meals"]

        daily_totals = state.nutrition_result.get("daily_totals", {})
        logger.info(f"✓ Daily total: {daily_totals.get('total_calories', 0)} calories")
        logger.info(f"✓ Daily protein: {daily_totals.get('total_protein_g', 0)}g")
        logger.info(f"✓ Daily carbs: {daily_totals.get('total_carbs_g', 0)}g")
        logger.info(f"✓ Daily fat: {daily_totals.get('total_fat_g', 0)}g")

        _record_trace(state, "nutrition_analysis.complete", daily_totals)

    def execute_format_output() -> None:
        logger.info("📝 STEP: format_output started")
        _record_trace(state, "format_output.start", {"meal_count": len(state.meals)})

        base_output = output_agent.run(state.meals)
        total_calories = estimate_total_calories(state.meals)

        footer_lines = [f"Total Estimated Calories: {total_calories} kcal"]
        if isinstance(state.target_calories, int) and state.target_calories > 0:
            delta = total_calories - state.target_calories
            direction = "above" if delta > 0 else "below"
            footer_lines.append(
                f"Target Comparison: {abs(delta)} kcal {direction} target ({state.target_calories} kcal)"
            )
            _record_trace(
                state,
                "format_output.branch.target_comparison",
                {"target_calories": state.target_calories, "actual_calories": total_calories, "delta": delta},
            )
        else:
            footer_lines.append("Target Comparison: skipped (no explicit calorie target)")
            _record_trace(state, "format_output.branch.target_comparison_skipped", {"target_calories": 0})

        state.final_output = add_footer(base_output, total_calories)
        state.final_output += "\n" + "\n".join(footer_lines[1:])

        logger.info("✓ format_output completed")
        _record_trace(state, "format_output.complete", {"output_length": len(state.final_output)})

    step_handlers: dict[str, Callable[[], None]] = {
        "meal_generation": execute_meal_generation,
        "nutrition_analysis": execute_nutrition_analysis,
        "format_output": execute_format_output,
    }

    # ============================================
    # Execute coordinator-selected workflow dynamically
    # ============================================
    for step in state.steps:
        handler = step_handlers.get(step)
        if not handler:
            warning_message = f"Unknown workflow step skipped: {step}"
            logger.warning(warning_message)
            state.errors.append(warning_message)
            _record_trace(state, "workflow.step_skipped", {"step": step})
            continue

        logger.info(f"➡️ Handoff to step: {step}")
        try:
            handler()
            state.executed_steps.append(step)
            logger.info(f"✅ Step completed: {step}")
        except Exception as error:
            error_message = f"Step failed ({step}): {error}"
            logger.exception(error_message)
            state.errors.append(error_message)
            _record_trace(state, "workflow.step_failed", {"step": step, "error": str(error)})
            raise

    # ============================================
    # COMPLETE
    # ============================================
    logger.info("=" * 60)
    logger.info("✅ Meal planning pipeline completed successfully!")
    logger.info(f"Executed steps: {state.executed_steps}")
    logger.info("=" * 60)
    
    print("\n" + "=" * 60)
    print("🍽️ YOUR PERSONALIZED MEAL PLAN")
    print("=" * 60)
    print(state.final_output)
    print("=" * 60)
    
    return state.final_output


def run_with_detailed_logging() -> str:
    """
    Alternative run function with more detailed logging for debugging.
    Useful for testing your Nutrition Agent specifically.
    """
    setup_logging()
    
    logger.info("🐛 Running in DETAILED DEBUG mode")
    
    state = PlannerState()
    
    # Test input
    test_input = "I want a high protein meal plan for weight loss using chicken and eggs"
    logger.info(f"Test input: {test_input}")
    
    coordinator = CoordinatorAgent()
    parsed = coordinator.run(test_input)
    
    meal_agent = MealAgent()
    meals = meal_agent.run(parsed)
    
    # YOUR AGENT - with detailed logging
    nutrition_agent = NutritionAgent()
    
    for meal in meals:
        logger.info(f"Processing meal: {meal.get('name')}")
        logger.info(f"  Description: {meal.get('description')}")
    
    result = nutrition_agent.run(meals)
    
    print("\n🔬 DETAILED NUTRITION OUTPUT:")
    for meal in result["meals"]:
        print(f"\n📌 {meal['name']}")
        print(f"   Description: {meal.get('description', 'N/A')}")
        print(f"   📊 Nutrition:")
        print(f"      Calories: {meal['nutrition']['calories']} cal")
        print(f"      Protein: {meal['nutrition']['protein_g']}g")
        print(f"      Carbs: {meal['nutrition']['carbs_g']}g")
        print(f"      Fat: {meal['nutrition']['fat_g']}g")
        print(f"      Confidence: {meal['nutrition']['confidence']}")
    
    print(f"\n📈 DAILY TOTALS:")
    print(f"   Total Calories: {result['daily_totals']['total_calories']} cal")
    print(f"   Total Protein: {result['daily_totals']['total_protein_g']}g")
    print(f"   Total Carbs: {result['daily_totals']['total_carbs_g']}g")
    print(f"   Total Fat: {result['daily_totals']['total_fat_g']}g")
    
    return result


if __name__ == "__main__":
    # Run the main system
    run_meal_planner_system()
    
    # Uncomment below to run detailed debug mode for YOUR agent
    # run_with_detailed_logging()
