"""Planner service facade used by the desktop app."""

from typing import Any, Callable

from main import run_meal_planner_request


ProgressCallback = Callable[[dict[str, Any]], None]


def run_planner_request(
    prompt: str,
    age: int,
    weight: int,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    return run_meal_planner_request(prompt, age, weight, progress_callback=progress_callback)
