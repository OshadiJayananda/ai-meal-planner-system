"""Main entry point for Meal Planner MAS - Nutrition Agent Integration"""

import logging
from typing import Dict, List, Any

from agents.coordinator import CoordinatorAgent
from agents.meal_agent import MealAgent
from agents.nutrition_agent import NutritionAgent  # YOUR updated agent
from agents.output_agent import OutputAgent
from state import PlannerState
from tools.format_tool import add_footer
from tools.input_tool import get_user_input
from tools.nutrition_tool import estimate_total_calories  # YOUR tool
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Setup logging configuration for observability."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("meal_planner.log", encoding='utf-8'),  # Log to file
            logging.StreamHandler(sys.stdout)  # Fixed: Use reconfigured stdout
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
    state.user_input = get_user_input()
    logger.info(f"User input: {state.user_input}")
    
    parsed = coordinator.run(state.user_input)
    
    state.goal = parsed.get("goal", "")
    state.ingredients = parsed.get("ingredients", [])
    state.avoid_ingredients = parsed.get("avoid_ingredients", [])
    state.target_calories = parsed.get("target_calories", 2000)
    state.diet_type = parsed.get("diet_type", "balanced")
    state.steps = parsed.get("steps", [])
    
    logger.info(f"✓ Goal: {state.goal}")
    logger.info(f"✓ Ingredients: {state.ingredients}")

    # ============================================
    # STEP 2: Generate meals with Meal Agent
    # ============================================
    logger.info("🍳 STEP 2: Generating meal suggestions...")
    state.meals = meal_agent.run(parsed)
    logger.info(f"✓ Generated {len(state.meals)} meals")

    # ============================================
    # STEP 3: YOUR NUTRITION AGENT - Calculate nutrition
    # ============================================
    logger.info("🧮 STEP 3: Calculating nutrition (YOUR AGENT)...")
    
    # YOUR AGENT in action!
    nutrition_result = nutrition_agent.run(state.meals)
    
    # Extract the enhanced meals and daily totals
    meals_with_nutrition = nutrition_result["meals"]
    daily_totals = nutrition_result["daily_totals"]
    
    logger.info(f"✓ Daily total: {daily_totals['total_calories']} calories")
    logger.info(f"✓ Daily protein: {daily_totals['total_protein_g']}g")
    logger.info(f"✓ Daily carbs: {daily_totals['total_carbs_g']}g")
    logger.info(f"✓ Daily fat: {daily_totals['total_fat_g']}g")

    # ============================================
    # STEP 4: Format output with Output Agent
    # ============================================
    logger.info("📝 STEP 4: Formatting final output...")
    base_output = output_agent.run(meals_with_nutrition)
    
    # Add footer with total calories (using YOUR tool)
    total_calories = estimate_total_calories(meals_with_nutrition)
    state.final_output = add_footer(base_output, total_calories)

    # ============================================
    # COMPLETE
    # ============================================
    logger.info("=" * 60)
    logger.info("✅ Meal planning pipeline completed successfully!")
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