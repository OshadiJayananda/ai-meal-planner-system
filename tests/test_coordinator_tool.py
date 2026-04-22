import unittest

from tools.coordinator_tool import normalize_parsed_data, select_workflow_steps


class TestCoordinatorTool(unittest.TestCase):

    def test_normalize_parsed_data_with_garbage_values(self):
        parsed = {
            "goal": "",
            "ingredients": ["  chicken  ", "", 123, " rice"],
            "avoid_ingredients": "pork",
            "target_calories": "1500",
            "diet_type": "",
            "steps": ["nutrition_analysis", "unknown_step", "format_output"],
        }

        normalized = normalize_parsed_data(parsed)

        self.assertEqual(normalized["goal"], "maintenance")
        self.assertEqual(normalized["diet_type"], "none")
        self.assertEqual(normalized["ingredients"], ["chicken", "rice"])
        self.assertEqual(normalized["avoid_ingredients"], [])
        self.assertEqual(normalized["target_calories"], 1500)
        self.assertEqual(normalized["steps"], ["nutrition_analysis", "format_output"])

    def test_normalize_parsed_data_defaults_steps_when_invalid(self):
        normalized = normalize_parsed_data({"steps": "meal_generation"})
        self.assertEqual(
            normalized["steps"],
            ["meal_generation", "nutrition_analysis", "format_output"],
        )

    def test_minimal_meal_request(self):
        parsed = {"target_calories": 0, "steps": []}
        steps = select_workflow_steps("Just give me meal ideas", parsed)
        self.assertEqual(steps, ["meal_generation"])

    def test_nutrition_focused_request(self):
        parsed = {"target_calories": 0, "steps": ["meal_generation"]}
        steps = select_workflow_steps(
            "Analyze calories of these meals: grilled chicken salad, tuna sandwich",
            parsed,
        )
        self.assertEqual(steps, ["nutrition_analysis", "format_output"])

    def test_full_pipeline_when_calorie_target_present(self):
        parsed = {"target_calories": 1500, "steps": ["meal_generation", "format_output"]}
        steps = select_workflow_steps("Give me meal plan around 1500 calories", parsed)
        self.assertEqual(steps, ["meal_generation", "nutrition_analysis", "format_output"])

    def test_llm_valid_combo_kept_for_non_calorie_request(self):
        parsed = {"target_calories": 0, "steps": ["meal_generation", "format_output"]}
        steps = select_workflow_steps("Plan meals with chicken and rice", parsed)
        self.assertEqual(steps, ["meal_generation", "format_output"])


if __name__ == "__main__":
    unittest.main()
