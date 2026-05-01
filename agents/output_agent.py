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
        
    def _format_user_profile(self, user: Dict[str, Any]) -> str:
        lines = []

        if user.get("goal") and user.get("goal") != "none":
            lines.append(f"- Goal: {user['goal']}")

        if user.get("diet_type") and user.get("diet_type") != "none":
            lines.append(f"- Diet Type: {user['diet_type']}")

        if isinstance(user.get("target_calories"), int) and user.get("target_calories", 0) > 0:
            lines.append(f"- Target Calories: {user['target_calories']} kcal")

        if user.get("ingredients"):
            lines.append(f"- Preferred Ingredients: {', '.join(user['ingredients'])}")

        if user.get("avoid_ingredients"):
            lines.append(f"- Avoid: {', '.join(user['avoid_ingredients'])}")

        return "\n".join(lines) if lines else "- No specific preferences provided"

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        user = data.get("user_profile", {})
        meals = data.get("meal_plan", [])
        totals = data.get("daily_totals", {})
        has_nutrition = data.get("has_nutrition", False)
        alignment_note = data.get("calorie_alignment", "")

        # ============================================
        # Build meal section dynamically
        # ============================================
        meal_text = ""
        for m in meals:
            meal_text += f"\nMeal Name: {m.get('name')}\n"
            meal_text += f"Type: {m.get('type')}\n"
            meal_text += f"Description: {m.get('description')}\n"

            if m.get("ingredients_used"):
                meal_text += f"Ingredients Used: {', '.join(m['ingredients_used'])}\n"

            if m.get("portion_guidance"):
                meal_text += f"Portion Guidance: {m.get('portion_guidance')}\n"

            if m.get("goal_fit"):
                meal_text += f"Goal Fit: {m.get('goal_fit')}\n"

            if m.get("alternatives"):
                meal_text += f"Alternatives: {', '.join(m['alternatives'])}\n"

            if has_nutrition and m.get("nutrition"):
                meal_text += f"Calories: {m['nutrition'].get('calories')} kcal\n"
                meal_text += f"Protein: {m['nutrition'].get('protein_g')} g\n"
                meal_text += f"Carbs: {m['nutrition'].get('carbs_g')} g\n"
                meal_text += f"Fat: {m['nutrition'].get('fat_g')} g\n"

        # ============================================
        # Nutrition section (ONLY if available)
        # ============================================
        if has_nutrition:
            nutrition_section = f"""
    Daily Totals:
    - Calories: {totals.get('total_calories', 'N/A')} kcal
    - Protein: {totals.get('total_protein_g', 'N/A')} g
    - Carbs: {totals.get('total_carbs_g', 'N/A')} g
    - Fat: {totals.get('total_fat_g', 'N/A')} g
    """
            nutrition_instruction = "- Include a Nutrition Summary section"
        else:
            nutrition_section = ""
            nutrition_instruction = "- DO NOT include Nutrition Summary\n- DO NOT mention calories or macros"

        # ============================================
        # Final Prompt
        # ============================================
        return f"""
Generate a clear and structured meal plan based ONLY on the provided data.

==============================
INPUT CONTEXT
==============================

User Profile:
{self._format_user_profile(user)}

Meals Provided:
{meal_text}

{nutrition_section}

Nutrition Availability:
- Has Nutrition Data: {has_nutrition}

Total Meals Provided: {len(meals)}

==============================
INSTRUCTIONS
==============================

Structure your response EXACTLY as follows:

==============================
🍽️ PERSONALIZED MEAL PLAN
==============================

👤 Profile Summary
- Goal: ...
- Diet Type: ...
- Target Calories: ...
- Preferred Ingredients: ...
- Avoid: ...

🍳 Meal Plan

For EACH meal, you MUST follow EXACTLY this format:

[Emoji] Meal Name
- Type: ...
- Description: ...
- Ingredients: ...
- Portion: ...
- Goal Fit: ...
- Alternatives: ... (if available)
- Calories: ... (ONLY if available)

Do NOT summarize meals into one line.

(IMPORTANT: Determine format based on number of meals)

- If Total Meals = 3:
  → Treat as ONE DAY plan:
    - Use the "Type" field to classify meals:
        Breakfast → 🥣
        Lunch → 🍛
        Dinner → 🍲
        Snack → 🥜
- If Total Meals > 3:
  → List meals sequentially WITHOUT creating days unless explicitly provided

📊 Nutrition Summary (ONLY if Has Nutrition Data = True)
- Calories: ...
- Protein: ...
- Carbs: ...
- Fat: ...
- Alignment: {alignment_note}

💡 Health Recommendations
- Provide simple, relevant advice

==============================
STRICT RULES (VERY IMPORTANT)
==============================
- DO NOT rewrite or summarize meals
- DO NOT change meal names
- DO NOT invent new descriptions
- You MUST use ALL provided fields (type, portion, goal_fit, alternatives)
- You are formatting data, NOT generating new content
- ONLY use the meals provided in input
- DO NOT create additional meals or days
- DO NOT assume a weekly plan
- DO NOT generate placeholders like:
  ❌ [Insert meal]
  ❌ "and so on"
- DO NOT fabricate missing data
- If nutrition data is NOT available:
  ❌ Do NOT show calories/macros anywhere
- If nutrition data IS available:
  ✅ Show calories per meal AND totals
- Keep output clean, spaced, and easy to read
- Use emojis for section headers
- Add one blank line between sections
- If a field exists in input, it MUST appear in output
- If a field does NOT exist, do NOT create it
"""