"""Main entry point for Meal Planner MAS - Nutrition Agent Integration"""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import logging
from typing import Any, Callable

from agents.coordinator import CoordinatorAgent
from agents.meal_agent import MealAgent
from agents.nutrition_agent import NutritionAgent
from agents.output_agent import OutputAgent
from state import PlannerState
from tools.format_tool import add_footer
from tools.input_tool import get_user_input
from tools.nutrition_tool import estimate_total_calories
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from db_service import (
    init_db,
    create_session,
    save_coordinator,
    save_meals,
    save_nutrition,
    save_final_output
)

logger = logging.getLogger(__name__)
DEFAULT_WORKFLOW_STEPS = ["meal_generation", "nutrition_analysis", "format_output"]
TRACE_REPORT_PATH = Path("trace_report.txt")


def _trace_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _record_trace(state: PlannerState, event: str, details: dict[str, Any] | None = None) -> None:
    """Append a lightweight structured trace event to shared state."""
    payload = {"timestamp": _trace_timestamp(), "event": event}
    if details:
        payload["details"] = details
    state.trace_events.append(payload)


def _trace_tool_event(
    state: PlannerState,
    tool_name: str,
    phase: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Record a structured tool-call trace event."""
    _record_trace(state, f"tool_call.{tool_name}.{phase}", details)


def _build_trace_report(state: PlannerState) -> str:
    """Build a human-readable trace report for the completed run."""
    lines: list[str] = []
    lines.append("TRACE REPORT")
    lines.append("=" * 60)

    if not state.trace_events:
        lines.append("No trace events were recorded.")
        return "\n".join(lines)

    event_times = [
        datetime.fromisoformat(event["timestamp"])
        for event in state.trace_events
        if event.get("timestamp")
    ]
    start_time = event_times[0] if event_times else None
    end_time = event_times[-1] if event_times else None
    duration_ms = int((end_time - start_time).total_seconds() * 1000) if start_time and end_time else 0

    lines.append(f"Generated at: {_trace_timestamp()}")
    lines.append(f"Total events: {len(state.trace_events)}")
    if start_time and end_time:
        lines.append(f"Trace span: {start_time.isoformat()} -> {end_time.isoformat()} ({duration_ms} ms)")
    lines.append(f"Executed steps: {', '.join(state.executed_steps) if state.executed_steps else 'none'}")
    lines.append(f"Errors: {len(state.errors)}")
    lines.append("")

    event_counts = Counter(event["event"] for event in state.trace_events)
    lines.append("Event counts:")
    for event_name, count in sorted(event_counts.items()):
        lines.append(f"- {event_name}: {count}")

    lines.append("")
    lines.append("Timeline:")
    for event in state.trace_events:
        details = event.get("details")
        detail_text = f" | {details}" if details else ""
        lines.append(f"- {event['timestamp']} | {event['event']}{detail_text}")

    lines.append("")
    lines.append("Inputs and outputs:")
    lines.append(f"- user_input: {state.user_input}")
    lines.append(f"- goal: {state.goal}")
    lines.append(f"- diet_type: {state.diet_type}")
    lines.append(f"- ingredients: {state.ingredients}")
    lines.append(f"- avoid_ingredients: {state.avoid_ingredients}")
    lines.append(f"- target_calories: {state.target_calories}")
    lines.append(f"- meals: {len(state.meals)}")
    lines.append(f"- final_output_length: {len(state.final_output)}")

    return "\n".join(lines)


def _write_trace_report(state: PlannerState, path: Path = TRACE_REPORT_PATH) -> str:
    """Print and persist the final trace report."""
    report = _build_trace_report(state)
    path.write_text(report, encoding="utf-8")
    logger.info("Trace report saved to %s", path)
    print("\n" + report)
    return report


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
    init_db()
    logger.info("=" * 60)
    logger.info("Starting Multi-Agent Meal Planner System")
    logger.info("=" * 60)

    # Initialize state
    state = PlannerState()

    # Initialize agents
    coordinator = CoordinatorAgent()
    meal_agent = MealAgent()
    nutrition_agent = NutritionAgent()
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

    session_id = create_session(state.user_input, state.age, state.current_weight)

    _record_trace(state, "coordinator.start", {"input": state.user_input})
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
            "input": state.user_input,
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

    save_coordinator(session_id, parsed)

    def execute_meal_generation() -> None:
        logger.info("🍳 STEP: meal_generation started")
        _record_trace(
            state,
            "meal_generation.start",
            {"input": {"goal": state.goal, "ingredients": state.ingredients, "diet_type": state.diet_type}},
        )

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

        save_meals(session_id, state.meals)
        _record_trace(state, "meal_generation.complete", {"meal_count": len(state.meals)})

    def execute_nutrition_analysis() -> None:
        logger.info("🧮 STEP: nutrition_analysis started")

        if not state.meals and state.ingredients:
            logger.info("🔧 Converting ingredients → meals for analysis")
            state.meals = [
                {"name": item, "description": f"{item} meal"}
                for item in state.ingredients
            ]

        _record_trace(state, "nutrition_analysis.start", {"input": {"meal_count": len(state.meals)}})

        state.nutrition_result = nutrition_agent.run(state.meals)
        state.meals = state.nutrition_result["meals"]

        daily_totals = state.nutrition_result.get("daily_totals", {})
        # Persist daily totals on shared state for downstream steps
        state.daily_totals = daily_totals
        logger.info(f"✓ Daily total: {daily_totals.get('total_calories', 0)} calories")
        logger.info(f"✓ Daily protein: {daily_totals.get('total_protein_g', 0)}g")
        logger.info(f"✓ Daily carbs: {daily_totals.get('total_carbs_g', 0)}g")
        logger.info(f"✓ Daily fat: {daily_totals.get('total_fat_g', 0)}g")

        save_nutrition(session_id, state.daily_totals)

        _record_trace(state, "nutrition_analysis.complete", daily_totals)

    def execute_format_output() -> None:
        logger.info("📝 STEP: format_output started")
        _record_trace(state, "format_output.start", {"input": {"meal_count": len(state.meals)}})

        # Compute totals first so they are available to the output formatter
        _trace_tool_event(state, "estimate_total_calories", "start", {"meal_count": len(state.meals)})
        total_calories = estimate_total_calories(state.meals)
        _trace_tool_event(state, "estimate_total_calories", "complete", {"result": total_calories})

        base_output = output_agent.run({
            "user_profile": {
                "goal": state.goal,
                "diet_type": state.diet_type,
                "target_calories": state.target_calories,
                "ingredients": state.ingredients,
                "avoid_ingredients": state.avoid_ingredients,
            },
            "meal_plan": state.meals,
            "daily_totals": {
                "total_calories": total_calories,
                "total_protein_g": state.daily_totals.get("total_protein_g", 0),
                "total_carbs_g": state.daily_totals.get("total_carbs_g", 0),
                "total_fat_g": state.daily_totals.get("total_fat_g", 0),
            }
        })

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
                {
                    "input": {"target_calories": state.target_calories, "actual_calories": total_calories},
                    "output": {"delta": delta, "direction": direction},
                },
            )
        else:
            footer_lines.append("Target Comparison: skipped (no explicit calorie target)")
            _record_trace(state, "format_output.branch.target_comparison_skipped", {"input": {"target_calories": 0}})

        state.final_output = add_footer(base_output, total_calories)
        state.final_output += "\n" + "\n".join(footer_lines[1:])

        save_final_output(session_id, state.final_output)

        logger.info("✓ format_output completed")
        _record_trace(state, "format_output.complete", {"output": {"output_length": len(state.final_output)}})

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
            _record_trace(state, "workflow.step_skipped", {"input": {"step": step}})
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
            _record_trace(state, "workflow.step_failed", {"input": {"step": step}, "error": str(error)})
            raise

    # ============================================
    # COMPLETE
    # ============================================
    logger.info("=" * 60)
    logger.info("✅ Meal planning pipeline completed successfully!")
    logger.info(f"Executed steps: {state.executed_steps}")
    logger.info("=" * 60)

    _write_trace_report(state)
    
    print("\n" + "=" * 60)
    print("🍽️ YOUR PERSONALIZED MEAL PLAN")
    print("=" * 60)
    print(state.final_output)
    print("=" * 60)
    
    return state.final_output

if __name__ == "__main__":
    # Run the main system
    run_meal_planner_system()
    
