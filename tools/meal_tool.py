"""Helper utilities for the meal generation agent."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


REQUIRED_MEAL_TYPES = ["Breakfast", "Lunch", "Dinner"]
OPTIONAL_MEAL_TYPES = ["Snack"]
ALL_MEAL_TYPES = REQUIRED_MEAL_TYPES + OPTIONAL_MEAL_TYPES
MEAL_ORDER = {meal_type: index for index, meal_type in enumerate(ALL_MEAL_TYPES)}
NON_VEGETARIAN_KEYWORDS = {
    "chicken",
    "beef",
    "pork",
    "fish",
    "salmon",
    "tuna",
    "shrimp",
    "mutton",
    "lamb",
    "turkey",
    "bacon",
    "sausage",
}
NON_VEGAN_KEYWORDS = NON_VEGETARIAN_KEYWORDS | {"egg", "eggs", "milk", "cheese", "yogurt", "butter"}
LIMIT_FOODS = {
    "kottu": "High oil and refined-carb dish; keep it to 1 small plate occasionally.",
    "biryani": "Energy-dense dish; keep it to 1 small plate and pair with vegetables.",
    "butter chicken": "Rich curry; limit to 3 to 4 tbsp gravy with a leaner protein portion.",
    "puuri": "Deep-fried food; keep it to 2 small pieces occasionally.",
    "fried food": "Best kept occasional and in small portions.",
}
AGE_WEIGHT_RANGES = [
    ("13-17 years, 40-55 kg", "3/4 to 1 cup carbs + 1 palm-size protein + 1/2 to 1 cup vegetables"),
    ("18-30 years, 45-60 kg", "1 to 1.25 cups carbs + 1 to 2 palm-size protein + 1 cup vegetables"),
    ("18-30 years, 60-80 kg", "1.25 to 1.5 cups carbs + 2 palm-size protein + 1 cup vegetables"),
    ("31-50 years, 50-75 kg", "1 to 1.25 cups carbs + 1 to 2 palm-size protein + 1 cup vegetables"),
    ("50+ years, 45-70 kg", "3/4 to 1 cup carbs + 1 palm-size protein + 1 cup vegetables"),
]


def normalize_ingredients(values: Iterable[str] | None) -> List[str]:
    """Normalize ingredient-like values while keeping insertion order."""
    normalized: List[str] = []
    seen = set()

    for value in values or []:
        if not isinstance(value, str):
            continue
        cleaned = value.strip().lower()
        if cleaned and cleaned not in seen:
            normalized.append(cleaned)
            seen.add(cleaned)

    return normalized


def validate_ingredients(ingredients: list) -> bool:
    """Return True when at least one usable ingredient exists."""
    return bool(normalize_ingredients(ingredients))


def contains_avoided_ingredient(text: str, avoid_ingredients: Iterable[str]) -> bool:
    """Check whether a text mentions any avoided ingredient."""
    haystack = (text or "").lower()
    return any(ingredient in haystack for ingredient in normalize_ingredients(avoid_ingredients))


def _violates_diet_type(text: str, diet_type: str) -> bool:
    haystack = (text or "").lower()
    normalized_diet = (diet_type or "none").strip().lower()

    if normalized_diet == "vegetarian":
        return any(keyword in haystack for keyword in NON_VEGETARIAN_KEYWORDS)

    if normalized_diet == "vegan":
        return any(keyword in haystack for keyword in NON_VEGAN_KEYWORDS)

    return False


def sanitize_meal_list(
    meals: Any,
    avoid_ingredients: Iterable[str] | None = None,
    diet_type: str = "none",
) -> List[Dict[str, Any]]:
    """Convert raw model output into a validated meal list."""
    sanitized: List[Dict[str, Any]] = []
    seen_required = set()
    snack_added = False

    for item in meals if isinstance(meals, list) else []:
        if not isinstance(item, dict):
            continue

        meal_type = str(item.get("type", "")).strip().title()
        if meal_type not in ALL_MEAL_TYPES:
            continue

        if meal_type in seen_required:
            continue

        if meal_type == "Snack" and snack_added:
            continue

        name = str(item.get("name", "")).strip()
        description = str(item.get("description", "")).strip()
        ingredients_used = normalize_ingredients(item.get("ingredients_used", []))

        if not name or not description:
            continue

        combined_text = " ".join([name, description, " ".join(ingredients_used)])
        if contains_avoided_ingredient(combined_text, avoid_ingredients or []):
            continue

        if _violates_diet_type(combined_text, diet_type):
            continue

        sanitized_item: Dict[str, Any] = {
            "name": name,
            "type": meal_type,
            "description": description,
        }
        if ingredients_used:
            sanitized_item["ingredients_used"] = ingredients_used
        for optional_key in ("portion_guidance", "goal_fit", "limit_note"):
            value = item.get(optional_key)
            if isinstance(value, str) and value.strip():
                sanitized_item[optional_key] = value.strip()
        alternatives = item.get("alternatives")
        if isinstance(alternatives, list):
            cleaned_alternatives = [str(value).strip() for value in alternatives if str(value).strip()]
            if cleaned_alternatives:
                sanitized_item["alternatives"] = cleaned_alternatives

        sanitized.append(sanitized_item)
        if meal_type == "Snack":
            snack_added = True
        else:
            seen_required.add(meal_type)

    return sorted(sanitized, key=lambda meal: MEAL_ORDER.get(meal["type"], 999))


def has_required_meal_types(meals: Iterable[Dict[str, Any]]) -> bool:
    """Ensure breakfast, lunch, and dinner exist exactly once."""
    found_types = {str(meal.get("type", "")).title() for meal in meals}
    return all(meal_type in found_types for meal_type in REQUIRED_MEAL_TYPES)


def build_fallback_meals(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Produce a deterministic, nutrition-agent-friendly fallback plan."""
    ingredients = normalize_ingredients(context.get("ingredients", []))
    avoid = normalize_ingredients(context.get("avoid_ingredients", []))
    goal = (context.get("goal") or "balanced").strip().lower() or "balanced"
    diet_type = (context.get("diet_type") or "none").strip().lower()
    requested_foods = normalize_ingredients(context.get("ingredients", []))
    age = _coerce_positive_number(context.get("age", 0))
    current_weight = _coerce_positive_number(context.get("current_weight", 0))

    protein = _pick_first_allowed(
        ingredients,
        avoid,
        preferred=["chicken", "eggs", "fish", "beans", "tofu"],
        default="tofu" if diet_type in {"vegetarian", "vegan"} else "chicken",
    )
    carb = _pick_first_allowed(
        ingredients,
        avoid,
        preferred=["rice", "oatmeal", "quinoa", "toast"],
        default="rice",
    )
    produce = _pick_first_allowed(
        ingredients,
        avoid,
        preferred=["vegetables", "broccoli", "spinach", "salad", "banana", "apple"],
        default="vegetables",
    )
    limit_note = _build_limit_note(requested_foods)
    goal_fit = "recommended" if "loss" in goal or "gain" in goal or "muscle" in goal else "balanced"
    breakfast_guidance = _build_portion_guidance("breakfast", goal, age, current_weight)
    lunch_guidance = _build_portion_guidance("lunch", goal, age, current_weight)
    dinner_guidance = _build_portion_guidance("dinner", goal, age, current_weight)

    breakfast = {
        "name": f"{produce.title()} {protein.title()} Bowl",
        "type": "Breakfast",
        "description": (
            f"A healthier breakfast bowl using {protein}, {carb}, and {produce}. "
            f"Suggested measure: {breakfast_guidance.split(';', 1)[0]}."
        ),
        "portion_guidance": breakfast_guidance,
        "goal_fit": goal_fit,
        "limit_note": limit_note,
        "alternatives": [f"If craving heavy street food, swap it for {carb} with {protein} and vegetables."],
    }
    lunch = {
        "name": f"{protein.title()} and {produce.title()} Lunch Plate",
        "type": "Lunch",
        "description": (
            f"A goal-friendly lunch plate with {protein}, {carb}, and {produce}. "
            f"Suggested measure: {lunch_guidance.split(';', 1)[0]}."
        ),
        "portion_guidance": lunch_guidance,
        "goal_fit": goal_fit,
        "limit_note": limit_note,
        "alternatives": [f"Replace oily meals with grilled or lightly cooked {protein} plus {carb}."],
    }
    dinner = {
        "name": f"Light {protein.title()} and {produce.title()} Dinner",
        "type": "Dinner",
        "description": (
            f"A lighter dinner featuring {protein}, {produce}, and a measured serving of {carb}. "
            f"Suggested measure: {dinner_guidance.split(';', 1)[0]}."
        ),
        "portion_guidance": dinner_guidance,
        "goal_fit": goal_fit,
        "limit_note": limit_note,
        "alternatives": [f"If eating rich curry, keep gravy to a few spoons and increase vegetables instead."],
    }

    meals: List[Dict[str, Any]] = [breakfast, lunch, dinner]

    if _should_add_snack(goal, context.get("target_calories")):
        snack_base = _pick_first_allowed(
            ingredients,
            avoid,
            preferred=["banana", "apple", "oatmeal", "eggs", "nuts"],
            default="fruit",
        )
        meals.append(
            {
                "name": f"{str(snack_base).title()} Snack",
                "type": "Snack",
                "description": (
                    f"An optional snack using {snack_base} in a small measured portion for extra satiety."
                ),
                "portion_guidance": _build_portion_guidance("snack", goal, age, current_weight),
                "goal_fit": "optional",
                "limit_note": limit_note,
                "alternatives": ["Choose fruit, dates, or a small handful of nuts instead of fried snacks."],
            }
        )

    return meals


def _pick_first_allowed(
    ingredients: List[str],
    avoid: List[str],
    preferred: List[str],
    default: str,
) -> str:
    for candidate in preferred:
        if candidate in ingredients and candidate not in avoid:
            return candidate
    return default


def _should_add_snack(goal: Any, target_calories: Any) -> bool:
    goal_text = str(goal or "").lower()
    if "muscle" in goal_text or "high protein" in goal_text:
        return True

    try:
        return int(target_calories or 0) >= 1800
    except (TypeError, ValueError):
        return False


def _build_limit_note(requested_foods: List[str]) -> str:
    notes = [note for food, note in LIMIT_FOODS.items() if food in requested_foods]
    if notes:
        return " ".join(notes)
    return "Use richer foods occasionally and keep oily gravies, fried items, and refined carbs in smaller portions."


def _build_portion_guidance(meal_type: str, goal: str, age: int, current_weight: int) -> str:
    meal_adjustment = {
        "breakfast": "Breakfast: 1 to 2 eggs or equivalent protein with the carb serving.",
        "lunch": "Lunch: keep vegetables at least 1 cup and curry gravy to a few spoons.",
        "dinner": "Dinner: use the lower end of the carb range and keep the meal lighter.",
        "snack": "Snack: 1 fruit, 2 dates, or a small handful of nuts.",
    }.get(meal_type, "")
    goal_note = (
        "For weight gain, use the upper end of the range."
        if "gain" in goal or "muscle" in goal
        else "For weight loss, use the lower end of the range."
    )
    if age > 0 and current_weight > 0:
        profile_label = f"Age {age} years, weight {current_weight} kg"
        personalized = _personalized_portion_from_profile(goal, current_weight)
        return f"{profile_label}: {personalized}; {meal_adjustment} {goal_note}".strip()

    ranges = " | ".join(f"{label}: {portion}" for label, portion in AGE_WEIGHT_RANGES)
    return f"{ranges}; {meal_adjustment} {goal_note}".strip()


def _coerce_positive_number(value: Any) -> int:
    try:
        number = int(value)
        return number if number > 0 else 0
    except (TypeError, ValueError):
        return 0


def _personalized_portion_from_profile(goal: str, current_weight: int) -> str:
    if current_weight < 50:
        base = "1 cup carbs + 1 palm-size protein + 1 cup vegetables"
    elif current_weight <= 65:
        base = "1.25 cups carbs + 1 to 2 palm-size protein + 1 cup vegetables"
    elif current_weight <= 80:
        base = "1.5 cups carbs + 2 palm-size protein + 1 cup vegetables"
    else:
        base = "1.5 to 2 cups carbs + 2 palm-size protein + 1 to 1.5 cups vegetables"

    if "gain" in goal or "muscle" in goal:
        return f"{base}; add 1 extra healthy fat source such as nuts or dates if tolerated"

    if "loss" in goal:
        return f"{base}; keep oils low and stay near the lower carb end"

    return base
