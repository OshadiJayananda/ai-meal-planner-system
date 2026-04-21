
import logging


logger = logging.getLogger(__name__)


def get_user_input() -> str:
    logger.info("Prompting user for meal plan request")
    print("\n--- Meal Plan Request ---")
    return input(
        "Describe your requirement (e.g., 'weight loss with rice, no beef, 1500 calories'): "
    ).strip()