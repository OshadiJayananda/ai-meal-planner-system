
def get_user_input() -> str:
    print("\n--- Meal Plan Request ---")
    return input(
        "Describe your requirement (e.g., 'weight loss with rice, no beef, 1500 calories'): "
    ).strip()