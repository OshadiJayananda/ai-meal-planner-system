
import logging


logger = logging.getLogger(__name__)


def get_user_input() -> tuple:
    logger.info("Prompting user for meal plan request")
    print("\n--- Meal Plan Request ---")
    request = input(
        "Describe your requirement (e.g., 'weight loss with rice, no beef, 1500 calories'): "
    ).strip()
    age = input("Enter your age in years (or press Enter to skip): ").strip()
    current_weight = input("Enter your current weight in kg (or press Enter to skip): ").strip()

    return request, age, current_weight