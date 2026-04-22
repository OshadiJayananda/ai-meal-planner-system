import os
import sys
import unittest
from unittest.mock import patch


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.meal_agent import MealAgent


class TestMealAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.context = {
            "goal": "weight loss",
            "ingredients": ["chicken", "rice", "eggs", "broccoli"],
            "avoid_ingredients": ["pork"],
            "target_calories": 1600,
            "age": 24,
            "current_weight": 58,
            "diet_type": "none",
        }

    def test_valid_llm_response_returns_required_meals(self) -> None:
        response = """
        [
          {"name": "Egg Rice Bowl", "type": "Breakfast", "description": "Eggs with rice and broccoli.", "ingredients_used": ["eggs", "rice", "broccoli"], "portion_guidance": "18-30 years, 45-60 kg: 1 cup rice + 2 eggs", "goal_fit": "recommended", "limit_note": "Limit fried foods.", "alternatives": ["Swap fried food for boiled eggs and rice"]},
          {"name": "Chicken Rice Plate", "type": "Lunch", "description": "Grilled chicken with rice and broccoli.", "ingredients_used": ["chicken", "rice", "broccoli"], "portion_guidance": "18-30 years, 60-80 kg: 1.5 cups rice + 2 palm-size chicken", "goal_fit": "recommended", "limit_note": "Keep gravy low.", "alternatives": ["Use grilled chicken instead of rich curry"]},
          {"name": "Chicken Broccoli Dinner", "type": "Dinner", "description": "Chicken with steamed broccoli and a small side of rice.", "ingredients_used": ["chicken", "broccoli", "rice"], "portion_guidance": "31-50 years, 50-75 kg: 1 cup rice + 1 palm-size chicken", "goal_fit": "recommended", "limit_note": "Keep dinner lighter.", "alternatives": ["Reduce rice at dinner if needed"]}
        ]
        """
        agent = MealAgent()
        with patch.object(agent, "_generate_with_crewai", return_value=response):
            meals = agent.run(self.context)

        self.assertEqual([meal["type"] for meal in meals], ["Breakfast", "Lunch", "Dinner"])
        self.assertTrue(all("description" in meal for meal in meals))
        self.assertTrue(all("portion_guidance" in meal for meal in meals))
        self.assertTrue(all("goal_fit" in meal for meal in meals))

    def test_optional_snack_is_preserved(self) -> None:
        response = """
        [
          {"name": "Egg Breakfast", "type": "Breakfast", "description": "Eggs and rice."},
          {"name": "Chicken Lunch", "type": "Lunch", "description": "Chicken and broccoli."},
          {"name": "Rice Dinner", "type": "Dinner", "description": "Rice with chicken and vegetables."},
          {"name": "Apple Snack", "type": "Snack", "description": "An apple for an optional snack."}
        ]
        """
        agent = MealAgent()
        with patch.object(agent, "_generate_with_crewai", return_value=response):
            meals = agent.run(self.context)

        self.assertEqual([meal["type"] for meal in meals], ["Breakfast", "Lunch", "Dinner", "Snack"])

    def test_avoided_ingredients_are_filtered_and_trigger_fallback(self) -> None:
        response = """
        [
          {"name": "Pork Breakfast", "type": "Breakfast", "description": "Pork with eggs."},
          {"name": "Chicken Lunch", "type": "Lunch", "description": "Chicken and rice."},
          {"name": "Chicken Dinner", "type": "Dinner", "description": "Chicken and broccoli."}
        ]
        """
        agent = MealAgent()
        with patch.object(agent, "_generate_with_crewai", return_value=response):
            meals = agent.run(self.context)

        combined = " ".join(f"{meal['name']} {meal['description']}" for meal in meals).lower()
        self.assertNotIn("pork", combined)
        self.assertEqual([meal["type"] for meal in meals[:3]], ["Breakfast", "Lunch", "Dinner"])

    def test_vegetarian_request_rejects_meat_and_uses_fallback(self) -> None:
        context = {
            "goal": "balanced",
            "ingredients": ["rice", "beans", "broccoli"],
            "avoid_ingredients": [],
            "target_calories": 1400,
            "diet_type": "vegetarian",
        }
        response = """
        [
          {"name": "Chicken Breakfast", "type": "Breakfast", "description": "Chicken with toast."},
          {"name": "Fish Lunch", "type": "Lunch", "description": "Fish with rice."},
          {"name": "Beef Dinner", "type": "Dinner", "description": "Beef and vegetables."}
        ]
        """
        agent = MealAgent()
        with patch.object(agent, "_generate_with_crewai", return_value=response):
            meals = agent.run(context)

        combined = " ".join(f"{meal['name']} {meal['description']}" for meal in meals).lower()
        self.assertNotIn("chicken", combined)
        self.assertNotIn("fish", combined)
        self.assertNotIn("beef", combined)

    def test_fallback_adds_portion_and_limit_guidance_for_heavy_foods(self) -> None:
        context = {
            "goal": "muscle gain",
            "ingredients": ["rice", "kottu", "butter chicken", "biryani", "eggs", "beans", "cashews"],
            "avoid_ingredients": [],
            "target_calories": 0,
            "diet_type": "none",
        }
        agent = MealAgent()

        with patch.object(agent, "_generate_with_crewai", return_value=""):
            with patch.object(agent, "_generate_with_ollama_client", return_value=""):
                meals = agent.run(context)

        self.assertTrue(all("portion_guidance" in meal for meal in meals[:3]))
        self.assertTrue(any("small plate" in meal.get("limit_note", "").lower() for meal in meals[:3]))
        self.assertTrue(any(meal.get("goal_fit") == "recommended" for meal in meals[:3]))

    def test_fallback_uses_exact_age_and_weight_when_provided(self) -> None:
        agent = MealAgent()

        with patch.object(agent, "_generate_with_crewai", return_value=""):
            with patch.object(agent, "_generate_with_ollama_client", return_value=""):
                meals = agent.run(self.context)

        self.assertTrue(all("Age 24 years, weight 58 kg" in meal.get("portion_guidance", "") for meal in meals[:3]))

    def test_malformed_json_uses_fallback(self) -> None:
        agent = MealAgent()
        with patch.object(agent, "_generate_with_crewai", return_value="[invalid json"):
            meals = agent.run(self.context)

        self.assertEqual([meal["type"] for meal in meals[:3]], ["Breakfast", "Lunch", "Dinner"])

    def test_crewai_failure_uses_fallback(self) -> None:
        agent = MealAgent()

        with patch.object(agent, "_generate_with_crewai", return_value=""):
            with patch.object(agent, "_generate_with_ollama_client", return_value=""):
                meals = agent.run(self.context)

        self.assertEqual([meal["type"] for meal in meals[:3]], ["Breakfast", "Lunch", "Dinner"])

if __name__ == "__main__":
    unittest.main()
