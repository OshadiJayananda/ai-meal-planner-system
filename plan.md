# SE4010 – CTSE

## Assignment 2 – Multi-Agent System (MAS)

---

## 📌 Project Overview

Your task is to **design, build, and deploy a locally-hosted Multi-Agent System (MAS)** that solves a **complex, multi-step real-world problem**.

- You can choose **any domain** (Finance, Healthcare, Education, etc.)
- This is **NOT a chatbot**
- The system should behave like a **team of intelligent agents working together**

---

## ⚙️ Technical Constraints (IMPORTANT)

Your system MUST:

- Run **fully locally** (no paid APIs)
- Use **Ollama (local LLMs)**
  - Example models: `llama3:8b`, `phi3`, `qwen`

- Use an **orchestration framework**:
  - LangGraph / CrewAI / AutoGen

❌ NOT allowed:

- OpenAI API
- Anthropic API
- Any paid cloud services

---

## 🧠 Core System Requirements

### 1. Multi-Agent Orchestration

- Use **3–4 agents minimum**
- Agents must interact (NOT isolated)
- Example pattern:
  - Coordinator → Worker → Evaluator

---

### 2. Tool Usage

Agents must use **custom Python tools**, such as:

- File read/write
- Database queries
- API calls (free/public only)
- Terminal commands

---

### 3. State Management

- Maintain a **global state**
- Pass data between agents without losing context

---

### 4. Observability (Logging)

- Track:
  - Inputs
  - Outputs
  - Tool usage

- Use logging/tracing instead of just print statements

---

## 👤 Individual Requirements (Per Student)

Each student MUST:

### 1. Build an Agent

- Define:
  - System prompt
  - Constraints
  - Role/persona

### 2. Build a Tool

- Python function with:
  - Type hints
  - Docstrings
  - Error handling

### 3. Testing / Evaluation

- Write test scripts
- Examples:
  - Property-based testing
  - LLM-as-a-Judge

---

## 📦 Deliverables

### 1. Source Code Repository

Include:

- MAS implementation
- 3–4 agents
- Custom tools
- Testing scripts

---

### 2. Demo Video (4–5 minutes)

Show:

- System workflow
- Key functionalities
- Must run locally

---

### 3. Technical Report (4–8 pages)

Include:

#### 📌 Sections

- Problem domain
- System architecture diagram
- Agent roles & workflow
- Agent design (prompts, logic)
- Tool descriptions
- State management
- Testing & evaluation
- GitHub link

#### 👨‍💻 Individual Contribution

Each member must show:

- Agent developed
- Tool implemented
- Challenges faced

---

## 📊 Assessment Criteria

### 🔹 System-Level (Total 50%)

| Criteria                          | Weight |
| --------------------------------- | ------ |
| Problem Definition & Architecture | 10%    |
| Multi-Agent Orchestration         | 15%    |
| Tool Development & Integration    | 10%    |
| State Management & Observability  | 10%    |
| Demo Video                        | 5%     |

---

### 🔹 Individual-Level (Total 50%)

| Criteria             | Weight |
| -------------------- | ------ |
| Testing & Evaluation | 10%    |
| Agent Design         | 20%    |
| Custom Tool          | 20%    |

---

## ✅ Key Tips to Score High

- Clearly define a **real-world problem**
- Use **proper agent collaboration (not linear scripts)**
- Build **useful tools (not dummy functions)**
- Implement **structured logging**
- Maintain **clean state passing**
- Add **good testing (not just happy path)**

---

## ❗ Important Notes

- Frontend is **NOT required**
- CLI-based system is completely acceptable
- Focus on **architecture and agent interaction**

---

## 🚀 Simple Example Idea

**AI Meal Planner MAS**

Agents:

1. Coordinator Agent
2. Nutrition Agent
3. Recipe Generator Agent
4. Formatter Agent

Tools:

- Nutrition calculator
- Recipe database fetcher

---

## 🎯 Final Goal

Build a system where:

> Multiple agents collaborate intelligently using tools and shared state to solve a real problem locally.

---

✅ If you build this correctly, you will easily score **high marks (80%+)**.
