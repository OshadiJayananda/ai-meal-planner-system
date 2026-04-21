"""Coordinator agent using CrewAI."""

import json

from crewai import Agent, Crew, LLM, Task

# Use CrewAI-native Ollama configuration to satisfy Agent.llm validation.
llm = LLM(model="ollama/llama3", base_url="http://localhost:11434")

# 1. Create Coordinator Agent
coordinator_agent = Agent(
    role="Coordinator",
    goal="Understand user request and plan the workflow",
    backstory="You manage other agents and decide the steps to generate a meal plan.",
    llm=llm,
    verbose=True
)


class CoordinatorAgent:
    """Coordinates the meal-planning flow using CrewAI."""

    def __init__(self):
        self.agent = coordinator_agent

    def run(self, user_input: str) -> dict:
        # 2. Create Coordinator Task
        task = Task(
            description=f"""
            Analyze the user request: "{user_input}"

            Extract the following:
            - goal (weight loss / muscle gain / maintenance)
            - ingredients (list)
            - avoid_ingredients (list)
            - target_calories (number if mentioned)
            - diet_type (vegetarian / vegan / none)

            Also decide workflow steps.

            Return ONLY valid JSON:
            {{
                "goal": "...",
                "ingredients": ["..."],
                "avoid_ingredients": ["..."],
                "target_calories": 0,
                "diet_type": "...",
                "steps": ["meal_generation", "nutrition_analysis", "format_output"]
            }}
            """,
            agent=self.agent,
            expected_output="Valid JSON with goal, ingredients, avoid_ingredients, target_calories, diet_type, and steps fields"
        )
        
        crew = Crew(agents=[self.agent], tasks=[task], verbose=False)
        result = crew.kickoff()

        # Crew output type may vary by version; prefer `raw` when available.
        response_text = str(getattr(result, "raw", result))

        try:
            parsed = json.loads(response_text)
        except Exception:
            try:
                start_index = response_text.index("{")
                end_index = response_text.rindex("}") + 1
                parsed = json.loads(response_text[start_index:end_index])
            except Exception:
                print("Failed to parse LLM output")
                parsed = {
                    "goal": "balanced",
                    "ingredients": [],
                    "avoid_ingredients": [],
                    "target_calories": None,
                    "diet_type": "none",
                    "steps": ["meal_generation", "nutrition_analysis", "format_output"]
                }

        return parsed
