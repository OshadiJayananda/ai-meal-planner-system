import json
import os
import sys
import unittest
from types import ModuleType
from types import SimpleNamespace
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
            "age": 24,
            "current_weight": 58,
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
        self.assertEqual(result["age"], 24)
        self.assertEqual(result["current_weight"], 58)
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
            "age": 21,
            "current_weight": 62,
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
        self.assertIsInstance(result["age"], int)
        self.assertIsInstance(result["current_weight"], int)
        self.assertIsInstance(result["steps"], list)

    def test_workflow_case_meal_and_format_when_no_calories(self):
        mock_response = json.dumps({
            "goal": "maintenance",
            "ingredients": ["chicken"],
            "avoid_ingredients": [],
            "target_calories": 0,
            "diet_type": "none",
            "steps": ["meal_generation", "nutrition_analysis", "format_output"]
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=mock_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("Give me a simple meal plan with chicken")

        self.assertEqual(result["steps"], ["meal_generation", "format_output"])

    def test_workflow_case_nutrition_and_format(self):
        mock_response = json.dumps({
            "goal": "maintenance",
            "ingredients": [],
            "avoid_ingredients": [],
            "target_calories": 0,
            "diet_type": "none",
            "steps": []
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=mock_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("Analyze calories of these meals")

        self.assertEqual(result["steps"], ["nutrition_analysis", "format_output"])

    def test_workflow_case_meal_only_minimal_request(self):
        mock_response = json.dumps({
            "goal": "maintenance",
            "ingredients": [],
            "avoid_ingredients": [],
            "target_calories": 0,
            "diet_type": "none",
            "steps": []
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=mock_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("Just give me meal ideas")

        self.assertEqual(result["steps"], ["meal_generation"])

    def test_nutrition_focused_request_overrides_llm_minimal_steps(self):
        mock_response = json.dumps({
            "goal": "maintenance",
            "ingredients": ["grilled chicken", "salad", "tuna", "yogurt"],
            "avoid_ingredients": [],
            "target_calories": 0,
            "diet_type": "none",
            "steps": ["meal_generation"]
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=mock_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("Analyze calories of these meals: grilled chicken salad, tuna sandwich, yogurt bowl")

        self.assertEqual(result["steps"], ["nutrition_analysis", "format_output"])

    def test_parses_json_from_prose_wrapped_response(self):
        wrapped_response = '''
Here is the extracted user request:

{
    "goal": "",
    "ingredients": ["grilled chicken", "salad", "tuna", "bread", "yogurt"],
    "avoid_ingredients": [],
    "target_calories": 0,
    "diet_type": ""
}

Since there are no specific goal, target calories, or diet type mentioned, I will use minimal workflow:

{
    "goal": "",
    "ingredients": ["grilled chicken", "salad", "tuna", "bread", "yogurt"],
    "avoid_ingredients": [],
    "target_calories": 0,
    "diet_type": "",
    "steps": ["meal_generation"]
}
'''

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=wrapped_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("Analyze calories of these meals: grilled chicken salad, tuna sandwich, yogurt bowl")

        self.assertIn("grilled chicken", result["ingredients"])
        self.assertEqual(result["steps"], ["nutrition_analysis", "format_output"])

    def test_blank_goal_and_diet_type_are_normalized(self):
        mock_response = json.dumps({
            "goal": "",
            "ingredients": ["grilled chicken salad", "tuna sandwich", "yogurt bowl"],
            "avoid_ingredients": [],
            "target_calories": 0,
            "diet_type": "",
            "steps": ["nutrition_analysis", "format_output"]
        })

        mock_crew = SimpleNamespace(
            kickoff=lambda: SimpleNamespace(raw=mock_response)
        )

        with patch("agents.coordinator.Crew", return_value=mock_crew):
            result = self.agent.run("Analyze calories of these meals: grilled chicken salad, tuna sandwich, yogurt bowl")

        self.assertEqual(result["goal"], "maintenance")
        self.assertEqual(result["diet_type"], "none")
        self.assertEqual(result["steps"], ["nutrition_analysis", "format_output"])

if __name__ == "__main__":
    unittest.main()
