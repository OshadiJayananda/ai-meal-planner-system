import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.coordinator import CoordinatorAgent


class TestCoordinatorAgent(unittest.TestCase):

    def setUp(self):
        self.agent = CoordinatorAgent()

    # Valid response test (STRICT validation)
    def test_valid_response(self):
        mock_response = json.dumps({
            "goal": "weight loss",
            "ingredients": ["chicken", "rice"],
            "avoid_ingredients": ["pork"],
            "target_calories": 1500,
            "diet_type": "none",
            "steps": ["meal_generation", "nutrition_analysis", "format_output"]
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=mock_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("weight loss with chicken and rice, no pork")

        self.assertEqual(result["goal"], "weight loss")
        self.assertEqual(result["ingredients"], ["chicken", "rice"])
        self.assertIn("pork", result["avoid_ingredients"])
        self.assertEqual(result["target_calories"], 1500)
        self.assertEqual(result["steps"], ["meal_generation", "nutrition_analysis", "format_output"])

    # Malformed JSON recovery
    def test_malformed_json(self):
        malformed = """
        {"goal": "weight loss", "ingredients": ["rice"],
         "steps": ["meal_generation", =format_output"]}
        """

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=malformed)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("simple meal")

        self.assertIn("goal", result)
        self.assertIsInstance(result["steps"], list)

    # Completely invalid JSON
    def test_invalid_json(self):
        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw="THIS IS NOT JSON")
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("random input")

        # Expect fallback behavior (adjust if your code differs)
        self.assertIsInstance(result, dict)

    # Missing fields handling
    def test_missing_fields(self):
        incomplete = json.dumps({
            "goal": "weight loss"
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=incomplete)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("weight loss")

        # Should not crash and should still return dict
        self.assertIn("goal", result)

    # Empty input
    def test_empty_input(self):
        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=json.dumps({}))
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("")

        self.assertIsInstance(result, dict)

    # Type validation
    def test_output_types(self):
        mock_response = json.dumps({
            "goal": "muscle gain",
            "ingredients": ["eggs"],
            "avoid_ingredients": [],
            "target_calories": 2000,
            "diet_type": "none",
            "steps": ["meal_generation", "nutrition_analysis", "format_output"]
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=mock_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("muscle gain with eggs")

        self.assertIsInstance(result["ingredients"], list)
        self.assertIsInstance(result["avoid_ingredients"], list)
        self.assertIsInstance(result["target_calories"], int)
        self.assertIsInstance(result["steps"], list)

if __name__ == "__main__":
    unittest.main()