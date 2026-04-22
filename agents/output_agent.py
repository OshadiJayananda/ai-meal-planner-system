import ollama
from typing import Dict, Any


class OutputAgent:
    def __init__(self):
        self.model = "llama3"

    def run(self, data: Dict[str, Any]) -> str:
        """
        Entry point from main.py
        """
        return self.generate_output(data)

    def generate_output(self, data: Dict[str, Any]) -> str:
        prompt = self._build_prompt(data)

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional nutritionist assistant. "
                            "Generate clear, structured, easy-to-read meal plans "
                            "for elderly users with health conditions."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response["message"]["content"]

        except Exception as e:
            return f"⚠️ Error generating output: {e}"

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        user = data.get("user_profile", {})
        meals = data.get("meal_plan", [])
        totals = data.get("daily_totals", {})

        # Build meal section
        meal_text = ""
        for m in meals:
            meal_text += f"""
{m.get('name', 'Meal')}:
- Description: {m.get('description')}
- Calories: {m.get('nutrition', {}).get('calories')} kcal
- Protein: {m.get('nutrition', {}).get('protein_g')} g
- Carbs: {m.get('nutrition', {}).get('carbs_g')} g
- Fat: {m.get('nutrition', {}).get('fat_g')} g
"""

        return f"""
Generate a professional meal plan.

User Profile:
- Goal: {user.get('goal')}
- Diet Type: {user.get('diet_type')}
- Target Calories: {user.get('target_calories')}
- Preferred Ingredients: {user.get('ingredients')}
- Avoid: {user.get('avoid_ingredients')}

Meals:
{meal_text}

Daily Totals:
- Calories: {totals.get('total_calories')} kcal
- Protein: {totals.get('total_protein_g')} g
- Carbs: {totals.get('total_carbs_g')} g
- Fat: {totals.get('total_fat_g')} g

Instructions:
1. Use clear headings
2. Sections:
   - Profile Summary
   - Meal Plan
   - Nutrition Summary
   - Health Recommendations
3. Use bullet points
4. Keep language simple for elderly users
5. Give advice based on goal and diet type
"""