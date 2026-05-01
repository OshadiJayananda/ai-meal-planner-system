# Repository Checklist

Status date: 2026-04-28

Use this checklist to track completion of SE4010 Assignment 2 requirements.

## System-Level Requirements

- [x] Problem domain selected and scoped (AI Meal Planner)
- [x] Runs locally with Python
- [x] Uses local Ollama-compatible models
- [x] Uses an orchestration framework (CrewAI)
- [x] Includes at least 3 agents
- [x] Includes 4 agents (Coordinator, Meal, Nutrition, Output)
- [x] Agent collaboration is non-trivial (coordinator selects workflow steps and agents hand off shared state)
- [x] Meal Agent is fully implemented (LLM-backed generation with validation and fallback)
- [x] Output Agent is fully implemented (LLM-backed final formatter)
- [x] Global state object exists
- [x] State is updated and consumed consistently by all agents
- [x] Logging is enabled (file + console)
- [x] Tool usage and agent handoffs are traceable in logs and trace report

## Tooling Requirements

- [x] Custom tool functions exist
- [x] Nutrition tool includes type hints and docstrings
- [x] Nutrition tool includes input validation and error handling
- [x] Additional meaningful tools implemented (coordinator, meal, input, format, and nutrition tools)
- [x] Tool integration covers multiple agents, not only one agent path

## Testing and Evaluation

- [x] Unit tests exist for nutrition tool behavior
- [x] Regression test exists for coordinator JSON parsing issue
- [x] Tests exist for Meal Agent behavior
- [ ] Tests exist for Output Agent behavior (missing)
- [ ] End-to-end pipeline tests exist (missing)
- [ ] Property-based tests included (missing)
- [x] LLM-as-a-Judge evaluation integrated into repeatable test flow

## Delivery Readiness

- [x] README includes setup + run + test instructions end-to-end
- [ ] Demo script/checklist prepared for 4-5 minute video (missing)
- [x] Architecture diagram prepared for report
- [x] Agent prompts/constraints documented per member contribution
- [x] Tool descriptions documented per member contribution
- [x] Challenges/lessons documented for report

## Quick Commands

```powershell
# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Run all tests
python -m unittest discover -s tests -p "test_*.py"

# Run app
python .\main.py
```
