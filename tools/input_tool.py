
def get_user_input() -> str:
    goal = input("What's your dietary goal (e.g., weight loss, muscle gain)? ")
    ingredients = input("Preferred ingredients (comma-separated): ")
    return f"I want a {goal} meal plan using {ingredients}"
