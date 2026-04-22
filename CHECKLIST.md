# Repository Checklist

Status date: 2026-04-22

Use this checklist to track completion of SE4010 Assignment 2 requirements.

## System-Level Requirements

- [x] Problem domain selected and scoped (AI Meal Planner)
- [x] Runs locally with Python
- [x] Uses local Ollama-compatible models
- [x] Uses an orchestration framework (CrewAI)
- [x] Includes at least 3 agents
- [x] Includes 4 agents (Coordinator, Meal, Nutrition, Output)
- [ ] Agent collaboration is non-trivial (beyond mostly linear pass-through)
- [ ] Meal Agent is fully implemented (not placeholder output)
- [ ] Output Agent is fully implemented (not placeholder formatter)
- [x] Global state object exists
- [ ] State is updated and consumed consistently by all agents
- [x] Logging is enabled (file + console)
- [ ] Tool usage and agent handoffs are fully traceable in logs

## Tooling Requirements

- [x] Custom tool functions exist
- [x] Nutrition tool includes type hints and docstrings
- [x] Nutrition tool includes input validation and error handling
- [ ] Additional meaningful tools implemented (beyond nutrition-only logic)
- [ ] Tool integration covers multiple agents, not only one agent path

## Testing and Evaluation

- [x] Unit tests exist for nutrition tool behavior
- [x] Regression test exists for coordinator JSON parsing issue
- [ ] Tests exist for Meal Agent behavior
- [ ] Tests exist for Output Agent behavior
- [ ] End-to-end pipeline tests exist
- [ ] Property-based tests included
- [x] LLM-as-a-Judge evaluation integrated into repeatable test flow

## Delivery Readiness

- [ ] README includes setup + run + test instructions end-to-end
- [ ] Demo script/checklist prepared for 4-5 minute video
- [ ] Architecture diagram prepared for report
- [ ] Agent prompts/constraints documented per member contribution
- [ ] Tool descriptions documented per member contribution
- [ ] Challenges/lessons documented for report

## Quick Commands

```powershell
# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Run all tests
python -m unittest discover -s tests -p "test_*.py"

# Run app
python .\main.py
```
