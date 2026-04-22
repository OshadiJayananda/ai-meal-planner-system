"""
Nutrition Agent for Meal Planner System
Author: Oshadi Jayananda
"""

import json
import logging
from typing import Dict, List, Any
from langchain_community.llms import Ollama

# Import YOUR custom tool
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tools.nutrition_tool import estimate_nutrition, calculate_daily_totals

logger = logging.getLogger(__name__)
class NutritionAgent:
    """
    Nutrition Expert Agent - Calculates nutritional information for meals.
    
    This agent uses a custom tool to estimate calories, protein, carbs, and fat
    for each meal suggested by the Meal Agent.
    """

    BATCH_INGREDIENT_SCHEMA = {
        "type": "object",
        "properties": {
            "meals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "meal_index": {"type": "integer"},
                        "ingredients": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["meal_index", "ingredients"]
                }
            }
        },
        "required": ["meals"]
    }
    
    def __init__(self, model: str = "llama3"):
        """
        Initialize the Nutrition Agent with Ollama LLM.
        
        Args:
            model: The Ollama model to use (default: llama3)
        """
        self.llm = Ollama(model=model)
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Nutrition Agent.
        
        Returns:
            str: The system prompt with constraints and persona
        """
        return """You are a Nutrition Expert Agent with 10+ years of experience.

YOUR PERSONA:
- Certified nutritionist
- Precise and data-driven
- Conservative in estimates
- Educational in explanations

RULES YOU MUST FOLLOW:
1. NEVER guess wildly — use standard nutritional databases
2. Always return nutrition in this EXACT format:
   {
     "meal_name": "string",
     "calories": int,
     "protein_g": int,
     "carbs_g": int,
     "fat_g": int,
     "confidence": "high|medium|low"
   }
3. If you don't know an ingredient, estimate using similar foods
4. For a full day, sum all meals
5. Be consistent — same meal = same nutrition
6. Flag meals with confidence = "low" for review

EXAMPLE OUTPUT:
For "Chicken Breast with Rice":
{"meal_name": "Chicken Breast with Rice", "calories": 450, "protein_g": 35, "carbs_g": 45, "fat_g": 12, "confidence": "high"}

Always use the estimate_nutrition tool to get accurate values.
"""

    def _extract_ingredients_with_llm(self, text: str) -> List[str]:
        """
        Use Ollama structured output to extract ingredients.
        """
        prompt = f"""
        Extract the main food ingredients from this meal:

        "{text}"

        Rules:
        - Return ONLY a JSON object with key "ingredients"
        - Ingredients must be SPECIFIC (not generic)
        - Do NOT return generic terms like "fruit", "food", "meal"

        - If a generic term appears, replace it with common specific items:
        - "fruit smoothie" → banana, milk
        - "fruit salad" → apple, banana
        - "vegetable dish" → carrot, beans
        - "smoothie" → banana, milk

        - Use simple base ingredient names only
        - No cooking styles (no "grilled", "fried")
        - No adjectives (no "fresh", "spicy")
        - Maximum 5 ingredients

        Examples:

        Input: "Fruit smoothie"
        Output: {{ "ingredients": ["banana", "milk"] }}

        Input: "Grilled chicken salad"
        Output: {{ "ingredients": ["chicken", "salad"] }}

        Output:
        """

        try:
            response = self.llm.invoke(
                prompt,
                format=self.INGREDIENT_SCHEMA
            )

            logger.info(f"  [LLM Response] {response}")

            if isinstance(response, dict):
                data = response
            else:
                data = json.loads(response)

            ingredients = data.get("ingredients", [])

            # basic cleanup
            ingredients = [i.strip().lower() for i in ingredients if i]

            return ingredients

        except Exception as e:
            logger.warning(f"Ingredient extraction failed: {e}")
            return []
 
    def _extract_ingredients_batch_with_llm(self, meal_texts: List[str]) -> Dict[int, List[str]]:
        """
        Use Ollama structured output to extract ingredients for multiple meals in one request.

        Args:
            meal_texts: List of meal descriptions

        Returns:
            Dict[int, List[str]] mapping meal index to extracted ingredients
        """
        numbered_meals = "\n".join(
            [f'{idx}: "{text}"' for idx, text in enumerate(meal_texts)]
        )

        prompt = f"""
        Extract the main food ingredients from these meals.

        Meals:
        {numbered_meals}

        Rules:
        - Return ONLY a JSON object with key "meals"
        - Each item must contain:
        - "meal_index": integer
        - "ingredients": array of strings
        - Ingredients must be SPECIFIC (not generic)
        - Do NOT return generic terms like "fruit", "food", "meal"
        - If a generic term appears, replace it with common specific items:
        - "fruit smoothie" -> banana, milk
        - "fruit salad" -> apple, banana
        - "vegetable dish" -> carrot, beans
        - "smoothie" -> banana, milk
        - Use simple base ingredient names only
        - No cooking styles (no "grilled", "fried")
        - No adjectives (no "fresh", "spicy")
        - Maximum 5 ingredients per meal

        Example output:
        {{
        "meals": [
            {{ "meal_index": 0, "ingredients": ["banana", "milk"] }},
            {{ "meal_index": 1, "ingredients": ["chicken", "salad"] }}
        ]
        }}

        Output:
        """

        try:
            response = self.llm.invoke(
                prompt,
                format=self.BATCH_INGREDIENT_SCHEMA
            )

            logger.info(f"  [Batch LLM Response] {response}")

            if isinstance(response, dict):
                data = response
            else:
                data = json.loads(response)

            result = {}
            for item in data.get("meals", []):
                meal_index = item.get("meal_index")
                ingredients = item.get("ingredients", [])

                if isinstance(meal_index, int):
                    cleaned_ingredients = [
                        i.strip().lower() for i in ingredients
                        if isinstance(i, str) and i.strip()
                    ]
                    result[meal_index] = cleaned_ingredients

            return result

        except Exception as e:
            logger.warning(f"Batch ingredient extraction failed: {e}")
            return {} 
 
    def run(self, meals: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"Nutrition Agent: Processing {len(meals)} meals")

        enhanced_meals = []

        meal_descriptions = [
            meal.get("description", meal.get("name", "Unknown Meal"))
            for meal in meals
        ]

        batch_ingredients = {}
        batch_called = False

        for idx, meal in enumerate(meals):
            meal_name = meal.get("name", "Unknown Meal")
            meal_description = meal.get("description", meal_name)

            ingredients = meal.get("ingredients_used", [])

            if not ingredients:
                if not batch_called:
                    logger.warning("⚠️ No ingredients from Meal Agent, using batch extraction")
                    logger.info(f"[Tool Call] _extract_ingredients_batch_with_llm")
                    batch_ingredients = self._extract_ingredients_batch_with_llm(meal_descriptions)
                    logger.info(f"[Tool Result] {batch_ingredients}")
                    batch_called = True

                ingredients = batch_ingredients.get(idx, [])

            if not ingredients:
                logger.warning(f"⚠️ Still missing ingredients for meal {idx}, using single extraction")
                ingredients = self._extract_ingredients_with_llm(meal_description)

            if ingredients:
                cleaned_input = " ".join(ingredients)
                logger.info(f"🔍 Using ingredients: {ingredients}")
            else:
                cleaned_input = meal_description
                logger.warning("⚠️ Using raw description")

            # Tool call
            logger.info(f"[Tool Call] estimate_nutrition('{cleaned_input}')")

            try:
                nutrition = estimate_nutrition(cleaned_input)
                logger.info(f"[Tool Result] {nutrition}")
                logger.info(f"  ✓ {meal_name}: {nutrition['calories']} cal (confidence: {nutrition['confidence']})")

            except Exception as e:
                logger.error(f"✗ Tool error for {meal_name}: {e}")
                nutrition = {
                    "meal_name": meal_name,
                    "calories": 400,
                    "protein_g": 15,
                    "carbs_g": 40,
                    "fat_g": 15,
                    "confidence": "low",
                    "ingredients_found": []
                }

            enhanced_meals.append({
                **meal,
                "nutrition": nutrition,
                "calories": nutrition.get("calories", 0)
            })

        # Daily totals
        logger.info("[Tool Call] calculate_daily_totals")
        daily_totals = calculate_daily_totals(enhanced_meals)
        logger.info(f"[Tool Result] {daily_totals}")
        logger.info(f"  Daily total: {daily_totals['total_calories']} calories")

        return {
            "meals": enhanced_meals,
            "daily_totals": daily_totals
        }    

    def run_with_llm_enhancement(self, meals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Advanced version: Use LLM to enhance nutrition estimates with explanations.
        
        Args:
            meals: List of meal dictionaries
        
        Returns:
            List of meals with enhanced nutrition information
        """
        base_result = self.run(meals)
        
        # Use LLM to add nutritional advice
        for meal in base_result["meals"]:
            nutrition = meal["nutrition"]
            
            prompt = f"""
            For a meal: {meal['name']}
            Nutrition: {nutrition['calories']} calories, {nutrition['protein_g']}g protein, 
                       {nutrition['carbs_g']}g carbs, {nutrition['fat_g']}g fat
            
            Give ONE sentence of nutritional advice (max 15 words).
            """
            
            try:
                advice = self.llm.invoke(prompt).strip()
                meal["nutrition_advice"] = advice
            except:
                meal["nutrition_advice"] = "Balanced meal option."
        
        return base_result