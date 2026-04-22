import json
import logging
import os
import re
import shutil
import subprocess
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

if "crewai" not in sys.modules:
    crewai_stub = ModuleType("crewai")

    class _CrewAIStub:
        def __init__(self, *args, **kwargs):
            pass

    crewai_stub.Agent = _CrewAIStub
    crewai_stub.Crew = _CrewAIStub
    crewai_stub.LLM = _CrewAIStub
    crewai_stub.Task = _CrewAIStub
    sys.modules["crewai"] = crewai_stub

from agents.coordinator import CoordinatorAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def has_ollama() -> bool:
    """Check whether the local ollama CLI is available."""
    return shutil.which("ollama") is not None


def call_ollama(prompt: str) -> str:
    """Call local Ollama model and return the model text output."""
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
        check=False,
    )
    return result.stdout.strip()


@unittest.skipUnless(has_ollama(), "Ollama CLI not found; skipping LLM judge tests")
class TestCoordinatorAgentLLMJudge(unittest.TestCase):
    @staticmethod
    def _build_mock_response_for_prompt(prompt: str) -> str:
        prompt_lower = prompt.lower()

        if "weight" in prompt_lower or "low calorie" in prompt_lower:
            goal = "weight loss"
        elif "muscle" in prompt_lower:
            goal = "muscle gain"
        else:
            goal = "maintenance"

        ingredients = []
        for keyword in ["rice", "chicken", "eggs", "vegetables", "beans"]:
            if keyword in prompt_lower:
                ingredients.append(keyword)

        avoid_ingredients = []
        if "no pork" in prompt_lower or ("avoid" in prompt_lower and "pork" in prompt_lower):
            avoid_ingredients.append("pork")
        if "no fried food" in prompt_lower or "avoid fried food" in prompt_lower:
            avoid_ingredients.append("fried food")

        calorie_match = re.search(r"(\d{3,4})\s*(kcal|calories)", prompt_lower)
        target_calories = int(calorie_match.group(1)) if calorie_match else 0
        age_match = re.search(r"age[:\s]+(\d{1,2})", prompt_lower)
        weight_match = re.search(r"(?:current\s+weight|weight)[:\s]+(\d{2,3})", prompt_lower)

        diet_type = "vegetarian" if "vegetarian" in prompt_lower else "none"

        return json.dumps(
            {
                "goal": goal,
                "ingredients": ingredients,
                "avoid_ingredients": avoid_ingredients,
                "target_calories": target_calories,
                "age": int(age_match.group(1)) if age_match else 0,
                "current_weight": int(weight_match.group(1)) if weight_match else 0,
                "diet_type": diet_type,
                "steps": ["meal_generation", "nutrition_analysis", "format_output"],
            }
        )

    def setUp(self) -> None:
        self.agent = CoordinatorAgent()

    def judge_output(self, user_prompt: str, agent_output: dict) -> tuple[bool, str]:
        judge_prompt = f"""
You are an evaluator.

Check only explicit constraints in the user request.
PASS if all explicit constraints are satisfied.
FAIL if any explicit constraint is violated or missing.
Do not penalize extra fields or details not requested.

User Request:
{user_prompt}

Agent Output:
{json.dumps(agent_output, indent=2)}

Answer ONLY:
PASS or FAIL
"""

        response = call_ollama(judge_prompt)
        return "PASS" in response.upper(), response

    def test_llm_judge_multiple_cases(self) -> None:

        test_prompts = [
            "I need a weight loss meal plan with chicken and rice around 1400 calories",
            "Create a vegetarian meal plan using beans and spinach, target 1500 kcal",
            
            "I want a weight loss meal plan using rice and chicken",
            "Give me a muscle gain meal plan with eggs and fish but no pork",
            
            "Analyze calories of these meals: grilled chicken salad, tuna sandwich",
            "Calculate macros for these meals: oatmeal with banana, chicken stir-fry",
            
            "Just give me meal ideas",
            "Only meal ideas with chicken and rice",
            
            "I want meal ideas and if possible show calories",
            "Analyze calories for these meals and suggest one better option"
        ]

        for prompt in test_prompts:
            with self.subTest(prompt=prompt):
                mock_response = self._build_mock_response_for_prompt(prompt)

                mock_crew = SimpleNamespace(
                    kickoff=lambda response=mock_response: SimpleNamespace(raw=response)
                )

                with patch("agents.coordinator.Crew", return_value=mock_crew):
                    result = self.agent.run(prompt)

                is_valid, response = self.judge_output(prompt, result)

                if not is_valid:
                    logger.error(f"FAIL for prompt: {prompt}")
                    logger.error(f"Result: {result}")
                    logger.error(f"Judge Response: {response}")

                self.assertTrue(is_valid, f"LLM judged FAIL for prompt: {prompt}")


if __name__ == "__main__":
    unittest.main()
