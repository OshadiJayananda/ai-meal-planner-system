# AI Meal Planner System

AI Meal Planner System is a multi-agent application that generates structured meal plans from user goals and ingredient constraints. It is designed to demonstrate practical agent orchestration with local LLM inference.

## Prerequisites

- Python 3.10 or newer
- [Ollama](https://ollama.com/) installed and running locally
- The `llama3` model pulled in Ollama

Pull the local model once before running the app:

```powershell
ollama pull llama3
```

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
- CustomTkinter desktop UI
- SQLite for local session/history storage

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

## Setup

From the project root, create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install project dependencies:

```powershell
pip install -r requirements.txt
```

Make sure Ollama is running in another terminal or as a background service:

```powershell
ollama serve
```

If `ollama serve` says Ollama is already running, you can continue.

## Run The Terminal App

Start the interactive command-line planner:

```powershell
python main.py
```

The app will ask for:

- A meal planning request
- Age, optional
- Current weight in kg, optional

Example request:

```text
Create a vegetarian meal plan using beans and spinach, target 1500 kcal
```

After a run, the app writes local output files such as:

- `meal_planner.db` for saved sessions
- `meal_planner.log` for runtime logs
- `trace_report.txt` for the latest workflow trace

## Run The Desktop App

The desktop app uses CustomTkinter and calls the local planner directly.

```powershell
python desktop_app.py
```

Use the prompt box or sidebar sample prompts, then click **Generate Meal Plan**.

## Build The Desktop Executable

PyInstaller is included in `requirements.txt`, and the repository includes `AI-Meal-Planner.spec`.

```powershell
pyinstaller AI-Meal-Planner.spec
```

The generated executable is written under `dist/`.

## Run Tests

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

Some tests call the local LLM through Ollama, so keep Ollama running when executing the full test suite.

## Checklist

Track assignment completion here:

- [CHECKLIST.md](CHECKLIST.md)

## License

For academic and demonstration use unless replaced by a project-specific license.
