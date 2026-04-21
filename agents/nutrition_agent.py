"""
Nutrition Agent for Meal Planner System
Author: [YOUR NAME]
"""

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
    
    def run(self, meals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate nutrition for each meal in the list.
        
        Args:
            meals: List of meal dictionaries from Meal Agent
                  Expected format: [{"name": "Breakfast", "description": "..."}, ...]
        
        Returns:
            List of meals with nutrition information added
        """
        logger.info(f"Nutrition Agent: Processing {len(meals)} meals")
        
        enhanced_meals = []
        
        for meal in meals:
            # Get meal name and description
            meal_name = meal.get("name", "Unknown Meal")
            meal_description = meal.get("description", meal_name)
            
            # Use YOUR custom tool to estimate nutrition
            try:
                nutrition = estimate_nutrition(meal_description)
                logger.info(f"  ✓ {meal_name}: {nutrition['calories']} cal (confidence: {nutrition['confidence']})")
            except Exception as e:
                logger.error(f"  ✗ Failed to estimate nutrition for {meal_name}: {e}")
                # Fallback values
                nutrition = {
                    "meal_name": meal_name,
                    "calories": 400,
                    "protein_g": 15,
                    "carbs_g": 40,
                    "fat_g": 15,
                    "confidence": "low",
                    "ingredients_found": []
                }
            
            # Combine original meal data with nutrition
            enhanced_meal = {
                **meal,  # Keep original meal data
                "nutrition": nutrition
            }
            enhanced_meals.append(enhanced_meal)
        
        # Calculate daily totals using YOUR second tool
        daily_totals = calculate_daily_totals(enhanced_meals)
        logger.info(f"  Daily total: {daily_totals['total_calories']} calories")
        
        # Add daily totals to the result
        result = {
            "meals": enhanced_meals,
            "daily_totals": daily_totals
        }
        
        return result
    
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