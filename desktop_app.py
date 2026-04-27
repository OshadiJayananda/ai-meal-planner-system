import queue
import threading
import traceback
from typing import Any

import customtkinter as ctk

from db_service import list_sessions
from main import run_meal_planner_request


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


SAMPLE_PROMPTS = [
    "Create a vegetarian meal plan using beans and spinach, target 1500 kcal",
    "I need a weight loss meal plan with chicken and rice around 1400 calories",
    "Analyze calories of these meals: oatmeal with banana, chicken stir-fry, lentil soup",
]


class MealPlannerDesktopApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("AI Meal Planner")
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.result_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_result_area()
        self._load_sessions()
        self.after(150, self._poll_result_queue)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, corner_radius=0, width=360)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.sidebar,
            text="AI Meal Planner",
            font=ctk.CTkFont(size=28, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, padx=24, pady=(28, 4), sticky="ew")

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Local multi-agent planner powered by Ollama",
            text_color="#52615a",
            anchor="w",
        )
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 22), sticky="ew")

        prompt_label = ctk.CTkLabel(self.sidebar, text="Meal request", font=ctk.CTkFont(weight="bold"), anchor="w")
        prompt_label.grid(row=2, column=0, padx=24, pady=(0, 8), sticky="ew")

        self.prompt_text = ctk.CTkTextbox(self.sidebar, height=150, wrap="word")
        self.prompt_text.grid(row=3, column=0, padx=24, sticky="ew")
        self.prompt_text.insert("1.0", SAMPLE_PROMPTS[0])

        profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        profile_frame.grid(row=4, column=0, padx=24, pady=16, sticky="ew")
        profile_frame.grid_columnconfigure((0, 1), weight=1)

        self.age_entry = self._labeled_entry(profile_frame, "Age", "22", 0)
        self.weight_entry = self._labeled_entry(profile_frame, "Weight kg", "70", 1)

        sample_label = ctk.CTkLabel(self.sidebar, text="Sample prompts", font=ctk.CTkFont(weight="bold"), anchor="w")
        sample_label.grid(row=5, column=0, padx=24, pady=(4, 8), sticky="ew")

        for index, prompt in enumerate(SAMPLE_PROMPTS, start=6):
            button = ctk.CTkButton(
                self.sidebar,
                text=prompt,
                anchor="w",
                fg_color="#e6f0e8",
                hover_color="#d5e8d9",
                text_color="#21352b",
                command=lambda value=prompt: self._set_prompt(value),
            )
            button.grid(row=index, column=0, padx=24, pady=4, sticky="ew")

        self.generate_button = ctk.CTkButton(
            self.sidebar,
            text="Generate Meal Plan",
            height=44,
            font=ctk.CTkFont(weight="bold"),
            command=self._generate_plan,
        )
        self.generate_button.grid(row=9, column=0, padx=24, pady=(18, 8), sticky="ew")

        self.status_label = ctk.CTkLabel(self.sidebar, text="Ready", text_color="#52615a", anchor="w")
        self.status_label.grid(row=10, column=0, padx=24, pady=(0, 14), sticky="ew")

        history_label = ctk.CTkLabel(self.sidebar, text="Recent sessions", font=ctk.CTkFont(weight="bold"), anchor="w")
        history_label.grid(row=11, column=0, padx=24, pady=(8, 8), sticky="ew")

        self.history_box = ctk.CTkScrollableFrame(self.sidebar, height=150)
        self.history_box.grid(row=12, column=0, padx=24, pady=(0, 20), sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)

    def _build_result_area(self) -> None:
        self.content = ctk.CTkFrame(self, fg_color="#f4f7f2", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self.metrics_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.metrics_frame.grid(row=0, column=0, padx=28, pady=(28, 14), sticky="ew")
        self.metrics_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.metric_labels = {
            "calories": self._metric_card("Calories", "0", "kcal", 0),
            "protein": self._metric_card("Protein", "0", "g", 1),
            "carbs": self._metric_card("Carbs", "0", "g", 2),
            "fat": self._metric_card("Fat", "0", "g", 3),
        }

        workflow_frame = ctk.CTkFrame(self.content, fg_color="white", corner_radius=8)
        workflow_frame.grid(row=1, column=0, padx=28, pady=(0, 14), sticky="ew")
        workflow_frame.grid_columnconfigure(0, weight=1)

        self.workflow_label = ctk.CTkLabel(
            workflow_frame,
            text="Workflow: Coordinator -> Meal Generator -> Nutrition Expert -> Output Formatter",
            anchor="w",
            text_color="#334139",
        )
        self.workflow_label.grid(row=0, column=0, padx=16, pady=12, sticky="ew")

        self.output_text = ctk.CTkTextbox(self.content, wrap="word", font=ctk.CTkFont(size=14))
        self.output_text.grid(row=2, column=0, padx=28, pady=(0, 28), sticky="nsew")
        self.output_text.insert("1.0", "Your generated meal plan will appear here.")

    def _labeled_entry(self, parent: ctk.CTkFrame, label: str, value: str, column: int) -> ctk.CTkEntry:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=column, padx=(0, 8) if column == 0 else (8, 0), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text=label, anchor="w").grid(row=0, column=0, sticky="ew")
        entry = ctk.CTkEntry(frame)
        entry.grid(row=1, column=0, pady=(6, 0), sticky="ew")
        entry.insert(0, value)
        return entry

    def _metric_card(self, title: str, value: str, suffix: str, column: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(self.metrics_frame, fg_color="white", corner_radius=8)
        card.grid(row=0, column=column, padx=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=title, text_color="#667085", anchor="w").grid(
            row=0, column=0, padx=16, pady=(14, 0), sticky="ew"
        )
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=26, weight="bold"), anchor="w")
        value_label.grid(row=1, column=0, padx=16, pady=(4, 0), sticky="ew")
        ctk.CTkLabel(card, text=suffix, text_color="#52615a", anchor="w").grid(
            row=2, column=0, padx=16, pady=(0, 14), sticky="ew"
        )
        return value_label

    def _set_prompt(self, prompt: str) -> None:
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)

    def _generate_plan(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            return

        prompt = self.prompt_text.get("1.0", "end").strip()
        if len(prompt) < 3:
            self.status_label.configure(text="Please enter a meal request.", text_color="#a8071a")
            return

        age = self._read_int(self.age_entry.get())
        weight = self._read_int(self.weight_entry.get())

        self.generate_button.configure(state="disabled", text="Generating...")
        self.status_label.configure(text="Agents are preparing your plan...", text_color="#52615a")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", "Generating meal plan. This can take a little while with local Ollama.")

        self.worker_thread = threading.Thread(
            target=self._run_planner_worker,
            args=(prompt, age, weight),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_planner_worker(self, prompt: str, age: int, weight: int) -> None:
        try:
            result = run_meal_planner_request(prompt, age, weight)
        except Exception:
            self.result_queue.put(("error", traceback.format_exc()))
            return

        self.result_queue.put(("success", result))

    def _poll_result_queue(self) -> None:
        try:
            status, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.after(150, self._poll_result_queue)
            return

        self.generate_button.configure(state="normal", text="Generate Meal Plan")

        if status == "error":
            self.status_label.configure(text="Generation failed. Check Ollama and terminal logs.", text_color="#a8071a")
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", payload)
        else:
            self._render_result(payload)
            self._load_sessions()

        self.after(150, self._poll_result_queue)

    def _render_result(self, result: dict[str, Any]) -> None:
        totals = result.get("daily_totals", {})
        self.metric_labels["calories"].configure(text=str(totals.get("total_calories", 0)))
        self.metric_labels["protein"].configure(text=str(totals.get("total_protein_g", 0)))
        self.metric_labels["carbs"].configure(text=str(totals.get("total_carbs_g", 0)))
        self.metric_labels["fat"].configure(text=str(totals.get("total_fat_g", 0)))

        steps = result.get("executed_steps", [])
        if steps:
            readable_steps = " -> ".join(step.replace("_", " ").title() for step in steps)
            self.workflow_label.configure(text=f"Workflow: {readable_steps}")

        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result.get("final_output", ""))
        self.status_label.configure(text=f"Saved session #{result.get('session_id')}", text_color="#246b45")

    def _load_sessions(self) -> None:
        for child in self.history_box.winfo_children():
            child.destroy()

        try:
            sessions = list_sessions(limit=8)
        except Exception:
            sessions = []

        if not sessions:
            ctk.CTkLabel(self.history_box, text="No saved sessions yet.", text_color="#667085").pack(anchor="w", padx=8, pady=8)
            return

        for session in sessions:
            label = ctk.CTkLabel(
                self.history_box,
                text=f"#{session['id']}  {session.get('goal') or 'meal plan'}\n{session['user_input']}",
                justify="left",
                anchor="w",
                text_color="#334139",
            )
            label.pack(fill="x", padx=8, pady=6)

    @staticmethod
    def _read_int(value: str) -> int:
        try:
            return int(value)
        except ValueError:
            return 0


if __name__ == "__main__":
    app = MealPlannerDesktopApp()
    app.mainloop()
