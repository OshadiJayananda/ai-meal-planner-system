"""Coordinator agent using CrewAI."""

import json
import logging
import re

from crewai import Agent, Crew, LLM, Task
from tools.coordinator_tool import DEFAULT_STEPS, normalize_parsed_data, select_workflow_steps


logger = logging.getLogger(__name__)

DEFAULT_COORDINATOR_RESPONSE = {
    "goal": "balanced",
    "ingredients": [],
    "avoid_ingredients": [],
    "target_calories": 0,
    "age": 0,
    "current_weight": 0,
    "diet_type": "none",
    "steps": DEFAULT_STEPS,
}

JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
STEPS_ARRAY_PATTERN = re.compile(r'("steps"\s*:\s*)\[(.*?)\]', re.DOTALL)

# Use CrewAI-native Ollama configuration to satisfy Agent.llm validation.
llm = LLM(model="ollama/llama3", base_url="http://localhost:11434")
#  ollama run phi3

# 1. Create Coordinator Agent
coordinator_agent = Agent(
    role="Coordinator",
    goal="Understand user request and plan the workflow",
    backstory="You manage other agents and decide the steps to generate a meal plan.",
    llm=llm,
    verbose=True
)


class CoordinatorAgent:
    """Coordinates the meal-planning flow using CrewAI."""

    def __init__(self):
        self.agent = coordinator_agent

    @staticmethod
    def _strip_code_fences(response_text: str) -> str:
        cleaned_text = response_text.strip()

        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(r"^```(?:json)?\s*", "", cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

        return cleaned_text.strip()

    @staticmethod
    def _extract_json_object_candidates(response_text: str) -> list[str]:
        cleaned_text = CoordinatorAgent._strip_code_fences(response_text)
        candidates: list[str] = [cleaned_text]
        decoder = json.JSONDecoder()

        for idx, char in enumerate(cleaned_text):
            if char != "{":
                continue

            try:
                parsed_obj, end_index = decoder.raw_decode(cleaned_text[idx:])
            except json.JSONDecodeError:
                continue

            if isinstance(parsed_obj, dict):
                candidates.append(cleaned_text[idx: idx + end_index])

        return candidates

    @staticmethod
    def _select_best_parsed_dict(parsed_candidates: list[dict]) -> dict:
        expected_keys = ("goal", "ingredients", "avoid_ingredients", "target_calories", "diet_type", "steps")

        def score(candidate: dict) -> tuple[int, int]:
            present_keys = sum(1 for key in expected_keys if key in candidate)
            has_steps = 1 if isinstance(candidate.get("steps"), list) else 0
            return has_steps, present_keys

        return max(parsed_candidates, key=score)

    @staticmethod
    def _repair_steps_array(response_text: str) -> str:
        def replace_steps(match: re.Match[str]) -> str:
            prefix = match.group(1)
            body = match.group(2)

            cleaned_steps: list[str] = []
            for raw_item in re.split(r"[\n,]", body):
                step_name = raw_item.strip().strip('"').strip("'").lstrip("=").strip()
                if step_name in DEFAULT_STEPS and step_name not in cleaned_steps:
                    cleaned_steps.append(step_name)

            if not cleaned_steps:
                cleaned_steps = DEFAULT_STEPS.copy()

            return prefix + json.dumps(cleaned_steps)

        return STEPS_ARRAY_PATTERN.sub(replace_steps, response_text, count=1)

    @staticmethod
    def _parse_response_text(response_text: str) -> dict:
        parsed_candidates: list[dict] = []
        text_candidates = CoordinatorAgent._extract_json_object_candidates(response_text)

        for candidate_text in text_candidates:
            for text_variant in (candidate_text, CoordinatorAgent._repair_steps_array(candidate_text)):
                try:
                    parsed = json.loads(text_variant)
                except json.JSONDecodeError:
                    continue

                if isinstance(parsed, dict):
                    parsed_candidates.append(parsed)

        if not parsed_candidates:
            logger.error(
                "Failed to parse LLM output; using fallback values. Raw response excerpt: %s",
                response_text[:250]
            )
            return DEFAULT_COORDINATOR_RESPONSE.copy()

        parsed = CoordinatorAgent._select_best_parsed_dict(parsed_candidates)
        return normalize_parsed_data(parsed)
    def run(self, user_input: str) -> dict:
        logger.info("Coordinator received user request")

        # 2. Create Coordinator Task
        task = Task(
            description=f"""
            Analyze the user request: "{user_input}"

            Extract the following:
            - goal (weight loss / muscle gain / maintenance)
            - ingredients (list)
            - avoid_ingredients (list)
            - target_calories (number if mentioned)
            - diet_type (vegetarian / vegan / none)

            ==============================
            IMPORTANT GENERAL RULES
            ==============================
            - If target calories are not explicitly mentioned, return 0 for target_calories.
            - Do NOT assume, infer, or guess values that are not explicitly provided.
            - If a field is not mentioned, leave it empty or default.

            ==============================
            INGREDIENT EXTRACTION RULES
            ==============================

            1. If the user provides FULL MEALS, keep them as full phrases.
            DO NOT split them into individual ingredients.

            Examples:
            - "grilled chicken salad" → ["grilled chicken salad"]
            - "tuna sandwich" → ["tuna sandwich"]
            - "yogurt bowl" → ["yogurt bowl"]

            2. If multiple meals are separated by commas:
            "grilled chicken salad, tuna sandwich, yogurt bowl"
            → ["grilled chicken salad", "tuna sandwich", "yogurt bowl"]

            3. Only extract individual ingredients when clearly mentioned:
            "meal plan with rice and chicken"
            → ["rice", "chicken"]

            4. DO NOT break meal names:
            ❌ ["grilled chicken", "salad"]
            ✅ ["grilled chicken salad"]

            5. Preserve meaningful phrases exactly as written.

            ==============================
            WORKFLOW STEP SELECTION
            ==============================

            You MUST choose ONLY from these options:

            1) ["meal_generation", "nutrition_analysis", "format_output"]
            Use when:
            - Full meal planning is required
            - AND nutrition analysis is needed
            - OR calorie target is provided

            2) ["meal_generation", "format_output"]
            Use when:
            - User wants meal planning only
            - No nutrition or calorie analysis required

            3) ["nutrition_analysis", "format_output"]
            MUST be used when:
            - User provides existing meals
            - AND asks to analyze calories, nutrition, or macros

            Examples:
            - "Analyze calories of these meals: grilled chicken salad, tuna sandwich"
            - "Calculate nutrition for my meals"
            - "Give macro breakdown for these meals"

            RULES:
            - DO NOT use "meal_generation"
            - DO NOT create new meals
            - ONLY analyze given meals

            4) ["meal_generation"]
            Use for minimal requests:
            - "just give me meal ideas"
            - "only meals"
            - "just meals"

            ==============================
            CRITICAL WORKFLOW RULE
            ==============================

            If the user provides meals AND asks for analysis:
            → ALWAYS return:
            ["nutrition_analysis", "format_output"]

            ==============================
            INGREDIENT vs MEAL RULE
            ==============================

            - If workflow is ["nutrition_analysis", "format_output"]:
            → ingredients MUST contain FULL MEAL NAMES

            - If workflow includes "meal_generation":
            → ingredients should be raw ingredients (e.g., rice, chicken)

            ==============================
            OUTPUT FORMAT RULES
            ==============================

            - Return ONLY valid JSON
            - Do NOT include explanations or extra text
            - Do NOT include multiple JSON objects
            - Return EXACTLY ONE JSON object

            ==============================
            RESPONSE FORMAT
            ==============================

            {{
                "goal": "...",
                "ingredients": ["..."],
                "avoid_ingredients": ["..."],
                "target_calories": 0,
                "diet_type": "...",
                "steps": ["meal_generation", "nutrition_analysis", "format_output"]
            }}
            """,
            agent=self.agent,
            expected_output="Valid JSON with goal, ingredients, avoid_ingredients, target_calories, diet_type, and steps fields"
        )
        
        crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
        result = crew.kickoff()

        # Crew output type may vary by version; prefer `raw` when available.
        response_text = str(getattr(result, "raw", result))
        logger.debug("Coordinator raw response: %s", response_text)
        parsed = self._parse_response_text(response_text)
        llm_suggested_steps = parsed.get("steps", [])
        parsed["steps"] = select_workflow_steps(user_input, parsed)
        logger.info(f"LLM suggested steps: {llm_suggested_steps}")
        logger.info(f"Final selected steps: {parsed['steps']}")

        return parsed