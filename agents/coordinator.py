"""Coordinator agent using CrewAI."""

import json
import logging
import re

from crewai import Agent, Crew, LLM, Task


logger = logging.getLogger(__name__)

DEFAULT_STEPS = ["meal_generation", "nutrition_analysis", "format_output"]
DEFAULT_COORDINATOR_RESPONSE = {
    "goal": "balanced",
    "ingredients": [],
    "avoid_ingredients": [],
    "target_calories": 0,
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
    def _extract_json_text(response_text: str) -> str:
        cleaned_text = CoordinatorAgent._strip_code_fences(response_text)
        json_match = JSON_OBJECT_PATTERN.search(cleaned_text)

        if json_match:
            return json_match.group(0)

        return cleaned_text

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
        candidate_text = CoordinatorAgent._extract_json_text(response_text)
        parsed = None

        for text_variant in (candidate_text, CoordinatorAgent._repair_steps_array(candidate_text)):
            try:
                parsed = json.loads(text_variant)
                break
            except json.JSONDecodeError:
                continue

        if not isinstance(parsed, dict):
            logger.exception("Failed to parse LLM output; using fallback values")
            return DEFAULT_COORDINATOR_RESPONSE.copy()

        parsed.setdefault("goal", DEFAULT_COORDINATOR_RESPONSE["goal"])
        parsed.setdefault("ingredients", [])
        parsed.setdefault("avoid_ingredients", [])
        parsed.setdefault("target_calories", 0)
        parsed.setdefault("diet_type", DEFAULT_COORDINATOR_RESPONSE["diet_type"])
        parsed_steps = parsed.get("steps", [])
        parsed["steps"] = [step for step in parsed_steps if step in DEFAULT_STEPS] or DEFAULT_STEPS.copy()

        return parsed

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

            Important rules:
            - If target calories are not explicitly mentioned, return 0 for target_calories.
            - Do NOT assume, infer, or guess values that are not explicitly provided.

            Also decide workflow steps.

            Return ONLY valid JSON:
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

        return self._parse_response_text(response_text)
