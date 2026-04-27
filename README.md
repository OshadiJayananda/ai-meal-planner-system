# AI Meal Planner System

AI Meal Planner System is a multi-agent application that generates structured meal plans from user goals and ingredient constraints. It is designed to demonstrate practical agent orchestration with local LLM inference.

## Repository Purpose

This repository showcases how a task can be split across specialized AI agents that collaborate in sequence to produce a final response.

Core idea:

- One agent coordinates intent extraction
- One agent generates meal suggestions
- One agent estimates nutrition details
- One agent formats a clear final output

## System Architecture

The system is organized around four roles:

1. Coordinator
2. Meal Generator
3. Nutrition Expert
4. Output Formatter

High-level workflow:

1. Parse user goal and ingredients
2. Generate candidate meals
3. Estimate calories per meal
4. Return polished meal plan output

## Tech Stack

- Python
- CrewAI (agent orchestration)
- Ollama with llama3 (local LLM)
- LangChain community Ollama integration

## Key Highlights

- Multi-agent design instead of single prompt execution
- Clear separation of responsibilities per agent
- Sequential orchestration for predictable outputs
- Local model inference via Ollama
- Suitable base for academic projects and portfolio demos

## Example Use Cases

- Weight loss meal planning with ingredient constraints
- Muscle gain meal suggestions with calorie estimates
- Quick weekly meal structure for simple household ingredients

## Project Scope

Current focus:

- Core multi-agent meal planning pipeline
- Goal and ingredient driven generation
- Approximate nutrition estimation
- Readable final presentation

Potential extensions:

- Tool usage for nutrition databases
- State management across user sessions
- Logging and observability
- Automated tests and evaluation scripts
- API and web interface integration

## Status

This repository represents a baseline, working multi-agent meal planner and serves as a foundation for further feature development.

## Running Tests

Run all unit tests from the project root:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Run only the Coordinator LLM-as-a-Judge test:

```powershell
python -m unittest tests/test_coordinator_llm_judge.py
```

Run only the Coordinator parser/unit test:

```powershell
python -m unittest .\tests\test_coordinator.py
```

## Running The Web App

Install backend dependencies:

```powershell
pip install -r requirements.txt
```

Start the FastAPI backend:

```powershell
uvicorn api:app --reload --port 8000
```

In a second terminal, start the React frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Running The Desktop App

The desktop frontend uses CustomTkinter and calls the local planner directly, so you do not need to run FastAPI or React for this mode.

Start Ollama first:

```powershell
ollama run llama3
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the desktop app:

```powershell
python desktop_app.py
```

## Checklist

Track assignment completion here:

- [CHECKLIST.md](CHECKLIST.md)

## License

For academic and demonstration use unless replaced by a project-specific license.
