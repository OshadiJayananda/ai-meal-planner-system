"""Coordinator routing utilities."""

import re


DEFAULT_STEPS = ["meal_generation", "nutrition_analysis", "format_output"]
STEP_CASE_FULL_PIPELINE = ["meal_generation", "nutrition_analysis", "format_output"]
STEP_CASE_MEAL_AND_FORMAT = ["meal_generation", "format_output"]
STEP_CASE_NUTRITION_AND_FORMAT = ["nutrition_analysis", "format_output"]
STEP_CASE_MEAL_ONLY = ["meal_generation"]

ALLOWED_STEP_COMBINATIONS = {
    tuple(STEP_CASE_FULL_PIPELINE),
    tuple(STEP_CASE_MEAL_AND_FORMAT),
    tuple(STEP_CASE_NUTRITION_AND_FORMAT),
    tuple(STEP_CASE_MEAL_ONLY),
}

CALORIE_MENTION_PATTERN = re.compile(r"\b\d{3,4}\s*(kcal|calories?|cal)\b", re.IGNORECASE)
NUTRITION_SIGNAL_PATTERN = re.compile(r"\b(calories?|nutrition|macros?|protein|carbs?|fat)\b", re.IGNORECASE)
NUTRITION_ACTION_PATTERN = re.compile(r"\b(analy[sz]e|calculate|estimate|breakdown|check|track)\b", re.IGNORECASE)


def normalize_parsed_data(parsed: dict) -> dict:
    """Normalize LLM output fields into a stable coordinator payload."""
    normalized: dict = parsed.copy() if isinstance(parsed, dict) else {}

    age = normalized.get("age", 0)
    if isinstance(age, int):
        normalized["age"] = age
    else:
        try:
            normalized["age"] = int(age)
        except (TypeError, ValueError):
            normalized["age"] = 0

    current_weight = normalized.get("current_weight", 0)
    if isinstance(current_weight, int):
        normalized["current_weight"] = current_weight
    else:
        try:
            normalized["current_weight"] = int(current_weight)
        except (TypeError, ValueError):
            normalized["current_weight"] = 0

    goal = normalized.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        normalized["goal"] = "maintenance"
    else:
        cleaned_goal = goal.strip().lower()
        normalized["goal"] = "maintenance" if cleaned_goal == "balanced" else cleaned_goal

    diet_type = normalized.get("diet_type")
    if not isinstance(diet_type, str) or not diet_type.strip():
        normalized["diet_type"] = "none"
    else:
        normalized["diet_type"] = diet_type.strip().lower()

    ingredients = normalized.get("ingredients")
    if isinstance(ingredients, list):
        normalized["ingredients"] = [item.strip() for item in ingredients if isinstance(item, str) and item.strip()]
    else:
        normalized["ingredients"] = []

    avoid_ingredients = normalized.get("avoid_ingredients")
    if isinstance(avoid_ingredients, list):
        normalized["avoid_ingredients"] = [
            item.strip()
            for item in avoid_ingredients
            if isinstance(item, str) and item.strip()
        ]
    else:
        normalized["avoid_ingredients"] = []

    target_calories = normalized.get("target_calories")
    if isinstance(target_calories, int):
        normalized["target_calories"] = target_calories
    else:
        try:
            normalized["target_calories"] = int(target_calories)
        except (TypeError, ValueError):
            normalized["target_calories"] = 0

    steps = normalized.get("steps")
    if isinstance(steps, list):
        normalized["steps"] = [step for step in _canonicalize_steps(steps) if step in DEFAULT_STEPS]
        if not normalized["steps"]:
            normalized["steps"] = DEFAULT_STEPS.copy()
    else:
        normalized["steps"] = DEFAULT_STEPS.copy()

    return normalized


def _canonicalize_steps(raw_steps: list[str] | tuple[str, ...] | None) -> list[str]:
    if not raw_steps:
        return []

    ordered: list[str] = []
    for step in DEFAULT_STEPS:
        if step in raw_steps and step not in ordered:
            ordered.append(step)

    return ordered


def _is_minimal_meal_request(user_input: str) -> bool:
    lowered = user_input.lower()
    minimal_phrases = (
        "just give me meal ideas",
        "just meal ideas",
        "only meal ideas",
        "just give meal ideas",
        "only meals",
        "just meals",
    )
    return any(phrase in lowered for phrase in minimal_phrases)


def _is_nutrition_focused_request(user_input: str) -> bool:
    has_action = bool(NUTRITION_ACTION_PATTERN.search(user_input))
    has_nutrition_signal = bool(NUTRITION_SIGNAL_PATTERN.search(user_input))
    mentions_existing_meals = any(
        marker in user_input.lower()
        for marker in ("these meals", "my meals", "this meal", "given meals")
    )
    return has_action and has_nutrition_signal and mentions_existing_meals


def select_workflow_steps(user_input: str, parsed_request: dict) -> list[str]:
    """Select the workflow steps for the coordinator based on rules and parsed request."""
    user_input = user_input or ""

    if _is_minimal_meal_request(user_input):
        return STEP_CASE_MEAL_ONLY.copy()

    if _is_nutrition_focused_request(user_input):
        return STEP_CASE_NUTRITION_AND_FORMAT.copy()

    target_calories = parsed_request.get("target_calories", 0)
    calorie_mentioned = isinstance(target_calories, int) and target_calories > 0
    if not calorie_mentioned:
        calorie_mentioned = bool(CALORIE_MENTION_PATTERN.search(user_input))

    if calorie_mentioned:
        return STEP_CASE_FULL_PIPELINE.copy()

    llm_steps = _canonicalize_steps(parsed_request.get("steps"))
    if tuple(llm_steps) in ALLOWED_STEP_COMBINATIONS and llm_steps != STEP_CASE_FULL_PIPELINE:
        return llm_steps

    return STEP_CASE_MEAL_AND_FORMAT.copy()
