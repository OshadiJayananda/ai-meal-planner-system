import os
import sys
import unittest

from unittest.mock import patch

# Ensure project root is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.output_agent import OutputAgent


class TestOutputAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = OutputAgent()

        self.sample_meal = {
            "name": "Sample Meal",
            "type": "Lunch",
            "description": "A simple test meal.",
            "ingredients_used": ["rice", "chicken"],
            "portion_guidance": "1 cup rice + 1 palm chicken",
            "goal_fit": "recommended",
            "alternatives": ["Use tofu for vegetarian option"],
            "nutrition": {"calories": 500, "protein_g": 35, "carbs_g": 50, "fat_g": 15},
        }

    def test_generate_output_returns_llm_content(self) -> None:
        data = {
            "user_profile": {"goal": "weight loss", "diet_type": "none"},
            "meal_plan": [self.sample_meal],
            "daily_totals": {"total_calories": 500, "total_protein_g": 35, "total_carbs_g": 50, "total_fat_g": 15},
            "has_nutrition": True,
            "calorie_alignment": "aligned",
        }

        fake_response = {"message": {"content": "LLM GENERATED OUTPUT"}}

        with patch("agents.output_agent.ollama.chat", return_value=fake_response):
            out = self.agent.generate_output(data)

        self.assertEqual(out, "LLM GENERATED OUTPUT")

    def test_generate_output_handles_exceptions(self) -> None:
        data = {"user_profile": {}, "meal_plan": [], "has_nutrition": False}

        with patch("agents.output_agent.ollama.chat", side_effect=Exception("API down")):
            out = self.agent.generate_output(data)

        self.assertTrue(isinstance(out, str))
        self.assertIn("⚠️ Error generating output:", out)

    def test_build_prompt_includes_nutrition_when_available(self) -> None:
        data = {
            "user_profile": {"goal": "balanced", "diet_type": "none"},
            "meal_plan": [self.sample_meal],
            "daily_totals": {"total_calories": 500, "total_protein_g": 35, "total_carbs_g": 50, "total_fat_g": 15},
            "has_nutrition": True,
            "calorie_alignment": "aligned",
        }

        prompt = self.agent._build_prompt(data)

        self.assertIn("Has Nutrition Data: True", prompt)
        self.assertIn("Daily Totals:", prompt)
        self.assertIn("Calories: 500 kcal", prompt)

    def test_build_prompt_excludes_nutrition_when_not_available(self) -> None:
        data = {"user_profile": {}, "meal_plan": [self.sample_meal], "has_nutrition": False}
        prompt = self.agent._build_prompt(data)

        self.assertIn("Has Nutrition Data: False", prompt)
        self.assertIn("DO NOT include Nutrition Summary", prompt)


if __name__ == "__main__":
    unittest.main()
