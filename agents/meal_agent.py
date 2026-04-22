"""Meal generation agent backed by a local Ollama model."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from tools.meal_tool import build_fallback_meals, has_required_meal_types, sanitize_meal_list

try:
    from crewai import Agent, Crew, LLM, Task
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    Agent = Crew = LLM = Task = None  # type: ignore[assignment]

try:
    from ollama import Client
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    Client = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

meal_llm = LLM(model="ollama/llama3", base_url="http://localhost:11434") if LLM is not None else None
meal_generation_agent = (
    Agent(
        role="Meal Generator",
        goal="Create a realistic one-day meal plan from structured user preferences",
        backstory=(
            "You design personalized meals that match the user's goal, ingredients, "
            "diet type, and food restrictions."
        ),
        llm=meal_llm,
        verbose=True,
    )
    if Agent is not None and meal_llm is not None
    else None
)


class MealAgent:
    """Generate a one-day meal plan using the parsed coordinator context."""

    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434") -> None:
        self.model = model
        self.host = host
        self.client = Client(host=host) if Client is not None else None
        self.agent = meal_generation_agent

    def run(self, context: dict, age: int, current_weight: float) -> list:
        """
        Input: parsed user context dict.
        Output: a list of meal dicts with required fields for downstream agents.
        """
        logger.info("Generating meal plan with Ollama model '%s'", self.model)

        fallback_meals = build_fallback_meals(context)
        response_text = self._generate_with_crewai(context, age, current_weight)

        if not response_text:
            response_text = self._generate_with_ollama_client(context)

        if not response_text:
            logger.warning("Meal generation produced no response; using fallback meals")
            return fallback_meals

        parsed_meals = self._parse_response(response_text, context)
        if parsed_meals:
            return parsed_meals

        logger.warning("Meal response was invalid; using fallback meals")
        return fallback_meals

    def _generate_with_crewai(self, context: Dict[str, Any], age: int, current_weight: float) -> str:
        if self.agent is None or Task is None or Crew is None:
            return ""

        ingredients = context.get("ingredients", [])
        avoid_ingredients = context.get("avoid_ingredients", [])
        goal = context.get("goal", "balanced")
        target_calories = context.get("target_calories", 0)
        age = context.get("age", 0)
        current_weight = context.get("current_weight", 0)
        diet_type = context.get("diet_type", "none")

        try:
            task = Task(
                description=f"""
                Create a one-day meal plan for this user:

                - Goal: {goal}
                - Preferred ingredients: {ingredients}
                - Avoid ingredients: {avoid_ingredients}
                - Target calories: {target_calories}
                - Age: {age}
                - Current weight (kg): {current_weight}
                - Diet type: {diet_type}

                Rules:
                - Return exactly 3 required meals: Breakfast, Lunch, Dinner
                - You may add 1 optional Snack only if it fits naturally
                - Respect avoid ingredients strictly
                - Respect diet type strictly
                - Use preferred ingredients where practical, but do NOT blindly repeat every food the user mentions
                - If the user mentions oily, fried, junk, or rich foods, do not build the whole plan around them
                - For unhealthy or rich foods, mention that they should be limited and give a small portion suggestion
                - Generate healthier meals that support the stated goal
                - If age and current weight are provided, use them directly for portion guidance
                - Only use broad age and weight ranges when age or current weight is missing
                - Keep meals realistic and simple
                - Each meal must have a short useful description

                Return ONLY valid JSON in this exact shape:
                [
                  {{
                    "name": "string",
                    "type": "Breakfast",
                    "description": "string",
                    "ingredients_used": ["string"],
                    "portion_guidance": "string",
                    "goal_fit": "recommended|limit|optional",
                    "limit_note": "string",
                    "alternatives": ["string"]
                  }},
                  {{
                    "name": "string",
                    "type": "Lunch",
                    "description": "string",
                    "ingredients_used": ["string"],
                    "portion_guidance": "string",
                    "goal_fit": "recommended|limit|optional",
                    "limit_note": "string",
                    "alternatives": ["string"]
                  }},
                  {{
                    "name": "string",
                    "type": "Dinner",
                    "description": "string",
                    "ingredients_used": ["string"],
                    "portion_guidance": "string",
                    "goal_fit": "recommended|limit|optional",
                    "limit_note": "string",
                    "alternatives": ["string"]
                  }}
                ]

                If you include a snack, add one more object with type "Snack".
                """,
                agent=self.agent,
                expected_output=(
                    "Valid JSON array of meal objects with name, type, description, ingredients_used, "
                    "portion_guidance, goal_fit, limit_note, and alternatives"
                ),
            )
            crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
            result = crew.kickoff()
            response_text = str(getattr(result, "raw", result)).strip()
            logger.debug("Meal agent raw CrewAI response: %s", response_text)
            return response_text
        except Exception as exc:
            logger.error("CrewAI meal generation failed; falling back to direct Ollama call: %s", exc)
            return ""

    def _generate_with_ollama_client(self, context: Dict[str, Any]) -> str:
        if self.client is None:
            logger.warning("Ollama Python client not available; using fallback meals")
            return ""

        try:
            prompt = self._build_prompt(context)
            response = self.client.generate(model=self.model, prompt=prompt)
            response_text = str(response.get("response", "")).strip()
            logger.debug("Meal agent raw Ollama response: %s", response_text)
            return response_text
        except Exception as exc:
            logger.error("Direct Ollama meal generation failed; using fallback meals: %s", exc)
            return ""

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        ingredients = context.get("ingredients", [])
        avoid_ingredients = context.get("avoid_ingredients", [])
        goal = context.get("goal", "balanced")
        target_calories = context.get("target_calories", 0)
        age = context.get("age", 0)
        current_weight = context.get("current_weight", 0)
        diet_type = context.get("diet_type", "none")

        return f"""
You are a meal planning assistant.

Create a one-day meal plan with:
- exactly 3 required meals: Breakfast, Lunch, Dinner
- optionally 1 Snack only if it naturally fits the day

User constraints:
- Goal: {goal}
- Preferred ingredients: {ingredients}
- Avoid ingredients: {avoid_ingredients}
- Target calories: {target_calories}
- Age: {age}
- Current weight (kg): {current_weight}
- Diet type: {diet_type}

Rules:
- Respect explicit avoid ingredients strictly
- Respect diet type strictly
- Use preferred ingredients where practical, but do NOT blindly repeat every food the user mentions
- If the user mentions oily, fried, junk, or rich foods, do not build the whole plan around them
- For unhealthy or rich foods, mention that they should be limited and give a small portion suggestion
- Generate healthier meals that support the stated goal
- If age and current weight are provided, use them directly for portion guidance
- Only use broad age and weight ranges when age or current weight is missing
- Keep meals realistic and simple
- Each meal must have a short useful description
- Return JSON only, with no markdown and no explanation text

Return this exact JSON shape:
[
  {{
    "name": "string",
    "type": "Breakfast",
    "description": "string",
    "ingredients_used": ["string"],
    "portion_guidance": "string",
    "goal_fit": "recommended|limit|optional",
    "limit_note": "string",
    "alternatives": ["string"]
  }},
  {{
    "name": "string",
    "type": "Lunch",
    "description": "string",
    "ingredients_used": ["string"],
    "portion_guidance": "string",
    "goal_fit": "recommended|limit|optional",
    "limit_note": "string",
    "alternatives": ["string"]
  }},
  {{
    "name": "string",
    "type": "Dinner",
    "description": "string",
    "ingredients_used": ["string"],
    "portion_guidance": "string",
    "goal_fit": "recommended|limit|optional",
    "limit_note": "string",
    "alternatives": ["string"]
  }}
]

If you include a snack, add one more object with type "Snack".
""".strip()

    @staticmethod
    def _extract_json_array(response_text: str) -> str:
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            return cleaned[start : end + 1]

        return cleaned

    def _parse_response(self, response_text: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        candidate = self._extract_json_array(response_text)

        try:
            decoded = json.loads(candidate)
        except json.JSONDecodeError:
            logger.exception("Failed to parse meal agent JSON output")
            return []

        sanitized = sanitize_meal_list(
            decoded,
            avoid_ingredients=context.get("avoid_ingredients", []),
            diet_type=str(context.get("diet_type", "none")),
        )

        if not has_required_meal_types(sanitized):
            return []

        return sanitized
