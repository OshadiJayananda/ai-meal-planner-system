import queue
import threading
import time
import traceback
import textwrap
from typing import Any

import customtkinter as ctk

from services.planner import run_planner_request
from services.session import list_recent_sessions, load_session_detail
from ui.output import build_output_panel, build_result_area, show_result_output, show_text_output
from ui.sidebar import build_session_history_card, build_sidebar
from ui.workflow import (
    build_workflow,
    configure_workflow_steps,
    get_visible_workflow_stages,
    reset_workflow,
    set_stage_state,
    set_workflow_expanded,
    update_workflow_state,
)


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


SAMPLE_PROMPTS = [
    "I need a weight loss meal plan with chicken and rice around 1400 calories",
    "I want a weight loss meal plan using rice and chicken",
    "Analyze calories of these meals: grilled chicken salad, tuna sandwich, yogurt bowl",
]


class MealPlannerDesktopApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("AI Meal Planner")
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.result_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.progress_messages: list[str] = []
        self.progress_events: list[dict[str, Any]] = []
        self.step_labels: dict[str, ctk.CTkLabel] = {}
        self.step_caption_labels: dict[str, ctk.CTkLabel] = {}
        self.workflow_stage_keys: list[str] = []
        self.selected_session_id: int | None = None
        self.request_started_at: float | None = None
        self.elapsed_timer_id: str | None = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        build_sidebar(self, SAMPLE_PROMPTS)
        build_result_area(self, SAMPLE_PROMPTS[0])
        build_workflow(self, self.content)
        build_output_panel(self, self.content)
        reset_workflow(self)
        self._load_sessions()
        self.after(150, self._poll_result_queue)

    def _set_prompt(self, prompt: str) -> None:
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)
        self._sync_request_preview()

    def _sync_request_preview(self, _event: object | None = None) -> None:
        prompt = self.prompt_text.get("1.0", "end").strip()
        hint = "Pick a sample prompt from the sidebar or write your own request here."
        if not prompt:
            hint = "Type a request to start building your meal plan."
        self.request_hint_label.configure(text=hint)

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
        self.clear_button.grid_remove()
        self.status_label.configure(text="Agents are preparing your plan...", text_color="#52615a")
        self._start_elapsed_timer()
        self._sync_request_preview()
        self.metrics_frame.grid_remove()
        self.request_focus_frame.grid()
        self.request_hint_label.configure(text="Current request is being analyzed by the coordinator.")
        reset_workflow(self)
        self.workflow_status.configure(text="Analyze user input")
        set_stage_state(self, "coordinator", "Analyze", "In progress", "active")
        self.progress_bar.set(0.12)
        self.progress_messages = []
        self.progress_events = []
        show_text_output(self, self._format_progress_log({"stage": "coordinator", "message": "Analyze user input"}))

        self.worker_thread = threading.Thread(
            target=self._run_planner_worker,
            args=(prompt, age, weight),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_planner_worker(self, prompt: str, age: int, weight: int) -> None:
        try:
            result = run_planner_request(
                prompt,
                age,
                weight,
                progress_callback=lambda event: self.result_queue.put(("progress", event)),
            )
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

        if status == "progress":
            self._render_progress(payload)
            self.after(150, self._poll_result_queue)
            return

        self.generate_button.configure(state="normal", text="Generate Meal Plan")

        if status == "error":
            self._stop_elapsed_timer()
            self.status_label.configure(text="Generation failed. Check Ollama and terminal logs.", text_color="#a8071a")
            self.workflow_status.configure(text="Generation failed. Check the error details below.")
            set_workflow_expanded(self, False)
            self.metrics_frame.grid_remove()
            self.request_focus_frame.grid()
            show_text_output(self, payload)
        else:
            self._render_result(payload)
            self._load_sessions()

        self.after(150, self._poll_result_queue)

    def _render_progress(self, event: dict[str, Any]) -> None:
        message = event.get("message", "Working")
        details = event.get("details", {})
        stage = event.get("stage", "")

        self.status_label.configure(text=message, text_color="#52615a")
        self.workflow_status.configure(text=message)
        update_workflow_state(self, stage, message)
        self._update_request_hint(stage, details)
        self._update_dynamic_workflow(stage, details)

        if not self.progress_messages or self.progress_messages[-1] != message:
            self.progress_messages.append(message)
            self.progress_events.append(event)

        show_text_output(self, self._format_progress_log(event))

    def _start_elapsed_timer(self) -> None:
        if self.elapsed_timer_id is not None:
            self.after_cancel(self.elapsed_timer_id)

        self.request_started_at = time.monotonic()
        self.elapsed_time_label.configure(text="Elapsed time: 00:00")
        self.elapsed_time_label.grid()
        self._refresh_elapsed_timer()

    def _refresh_elapsed_timer(self) -> None:
        if self.request_started_at is None:
            self.elapsed_timer_id = None
            return

        elapsed_seconds = int(time.monotonic() - self.request_started_at)
        self.elapsed_time_label.configure(text=f"Elapsed time: {self._format_elapsed_time(elapsed_seconds)}")
        self.elapsed_timer_id = self.after(500, self._refresh_elapsed_timer)

    def _reset_elapsed_timer(self) -> None:
        if self.elapsed_timer_id is not None:
            self.after_cancel(self.elapsed_timer_id)
            self.elapsed_timer_id = None

        self.request_started_at = None
        self.elapsed_time_label.configure(text="Elapsed time: 00:00")
        self.elapsed_time_label.grid_remove()

    def _stop_elapsed_timer(self) -> None:
        if self.elapsed_timer_id is not None:
            self.after_cancel(self.elapsed_timer_id)
            self.elapsed_timer_id = None

        if self.request_started_at is None:
            return

        elapsed_seconds = int(time.monotonic() - self.request_started_at)
        self.elapsed_time_label.configure(text=f"Completed in: {self._format_elapsed_time(elapsed_seconds)}")
        self.request_started_at = None

    @staticmethod
    def _format_elapsed_time(total_seconds: int) -> str:
        minutes, seconds = divmod(max(total_seconds, 0), 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        return f"{minutes:02d}:{seconds:02d}"

    def _update_request_hint(self, stage: str, details: dict[str, Any]) -> None:
        if stage != "coordinator" or not details:
            return

        hint_parts = []
        goal = details.get("goal")
        diet_type = details.get("diet_type")
        target_calories = details.get("target_calories")
        if goal:
            hint_parts.append(f"Goal: {goal}")
        if diet_type and diet_type != "none":
            hint_parts.append(f"Diet: {diet_type}")
        if target_calories:
            hint_parts.append(f"Target: {target_calories} kcal")

        if hint_parts:
            self.request_hint_label.configure(text=" • ".join(hint_parts))

    def _update_dynamic_workflow(self, stage: str, details: dict[str, Any]) -> None:
        steps = details.get("steps") if stage == "coordinator" else None
        if not isinstance(steps, list):
            return

        configure_workflow_steps(self, ["coordinator", *steps])
        for stage_key, title, caption in get_visible_workflow_stages(self):
            if stage_key == "coordinator":
                set_stage_state(self, stage_key, title, "Done", "done")
            else:
                set_stage_state(self, stage_key, title, caption, "pending")
        self.progress_bar.set(1 / max(len(self.workflow_stage_keys), 1))

    def _format_progress_log(self, current_event: dict[str, Any] | None = None) -> str:
        current_event = current_event or (self.progress_events[-1] if self.progress_events else {})
        current_message = current_event.get("message", "Preparing")
        current_details = current_event.get("details", {})

        lines = ["Agent progress", ""]
        lines.append(f"Current: {current_message}")

        current_summary = self._format_progress_summary(current_event.get("stage", ""), current_details)
        if current_summary:
            lines.append(current_summary)

        completed = self._completed_progress_items()
        if completed:
            lines.extend(["", "Completed"])
            lines.extend(f"- {item}" for item in completed)

        pending = self._pending_progress_items(current_event.get("stage", ""))
        if pending:
            lines.extend(["", "Next"])
            lines.extend(f"- {item}" for item in pending)

        return "\n".join(lines).strip()

    def _completed_progress_items(self) -> list[str]:
        completed: list[str] = []
        for event in self.progress_events:
            message = event.get("message", "")
            lowered = message.lower()
            if any(word in lowered for word in ("analyzed", "generated", "complete", "formatted")):
                completed.append(message)
        return completed

    def _pending_progress_items(self, current_stage: str) -> list[str]:
        labels = {
            "coordinator": "Generate or analyze meals",
            "meal_generation": "Analyze nutrition",
            "nutrition_analysis": "Format final output",
            "format_output": "Show final meal plan",
        }
        visible_stages = [stage for stage, _title, _caption in get_visible_workflow_stages(self)]
        if current_stage not in visible_stages:
            return []

        return [labels.get(stage, stage.replace("_", " ").title()) for stage in visible_stages[visible_stages.index(current_stage) + 1:]]

    def _format_progress_summary(self, stage: str, details: dict[str, Any]) -> str:
        if not details:
            return ""

        if stage == "coordinator" and "steps" not in details:
            return "Reading your request and profile."

        if stage == "coordinator" and "steps" in details:
            summary_parts = []
            if details.get("goal"):
                summary_parts.append(f"Goal: {details['goal']}")
            if details.get("diet_type") and details["diet_type"] != "none":
                summary_parts.append(f"Diet: {details['diet_type']}")
            if details.get("ingredients"):
                summary_parts.append(f"Items: {self._compact_list(details['ingredients'])}")
            if details.get("steps"):
                summary_parts.append(f"Workflow: {self._compact_step_names(details['steps'])}")
            return "\n".join(summary_parts)

        if stage == "nutrition_analysis":
            if "total_calories" in details:
                return (
                    f"Totals: {details.get('total_calories', 0)} kcal, "
                    f"{details.get('total_protein_g', 0)}g protein, "
                    f"{details.get('total_carbs_g', 0)}g carbs, "
                    f"{details.get('total_fat_g', 0)}g fat"
                )
            if details.get("meals"):
                return f"Analyzing {details.get('meal_count', len(details['meals']))} meals: {self._compact_list(details['meals'])}"

        if stage == "meal_generation" and details.get("meals"):
            return f"Created meals: {self._compact_list(details['meals'])}"

        if stage == "format_output" and details.get("meal_count"):
            return f"Preparing final plan for {details['meal_count']} meals."

        return self._format_progress_details(details)

    def _compact_list(self, value: list[Any]) -> str:
        return textwrap.shorten(", ".join(str(item) for item in value), width=130, placeholder="...")

    def _compact_step_names(self, steps: list[Any]) -> str:
        return " -> ".join(str(step).replace("_", " ").title() for step in steps)

    def _format_progress_details(self, details: dict[str, Any]) -> str:
        if not details:
            return ""

        lines: list[str] = []
        for key, value in details.items():
            if value in (None, "", [], {}):
                continue
            label = key.replace("_", " ").title()
            value_text = ", ".join(str(item) for item in value) if isinstance(value, list) else str(value)
            value_text = textwrap.shorten(value_text, width=180, placeholder="...")
            lines.append(f"   {label}: {value_text}")
        return "\n".join(lines)

    def _render_result(self, result: dict[str, Any]) -> None:
        totals = result.get("daily_totals", {})
        self.request_focus_frame.grid()
        self.metrics_frame.grid()
        self.progress_bar.set(1)
        self.workflow_status.configure(text="Meal plan ready.")
        set_workflow_expanded(self, False)
        if result.get("executed_steps"):
            configure_workflow_steps(self, ["coordinator", *result.get("executed_steps", [])])
        for stage, title, _caption in get_visible_workflow_stages(self):
            set_stage_state(self, stage, title, "Done", "done")

        self.metric_labels["calories"].configure(text=str(totals.get("total_calories", 0)))
        self.metric_labels["protein"].configure(text=str(totals.get("total_protein_g", 0)))
        self.metric_labels["carbs"].configure(text=str(totals.get("total_carbs_g", 0)))
        self.metric_labels["fat"].configure(text=str(totals.get("total_fat_g", 0)))

        steps = result.get("executed_steps", [])
        if steps:
            readable_steps = " -> ".join(step.replace("_", " ").title() for step in steps)
            self.workflow_label.configure(text=f"Completed workflow: {readable_steps}")

        show_result_output(self, result.get("final_output", ""))
        self._stop_elapsed_timer()
        self.status_label.configure(text=f"Saved session #{result.get('session_id')}", text_color="#246b45")
        self.selected_session_id = result.get("session_id")
        self.clear_button.configure(state="normal")
        self.clear_button.grid()

    def _clear_view(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            return

        self.selected_session_id = None
        self.progress_messages = []
        self.progress_events = []

        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", SAMPLE_PROMPTS[0])
        self.request_hint_label.configure(text="Pick a sample prompt from the sidebar or write your own request here.")

        self.metrics_frame.grid_remove()
        self.request_focus_frame.grid()
        configure_workflow_steps(self, ["coordinator", "meal_generation", "nutrition_analysis", "format_output"])
        reset_workflow(self)

        self.workflow_status.configure(text="Ready to analyze your meal request.")
        self.status_label.configure(text="Ready", text_color="#52615a")
        self._reset_elapsed_timer()

        self.metric_labels["calories"].configure(text="0")
        self.metric_labels["protein"].configure(text="0")
        self.metric_labels["carbs"].configure(text="0")
        self.metric_labels["fat"].configure(text="0")

        show_text_output(self, "Your meal plan will appear here after you generate a request.")
        self._refresh_history_selection()
        self.clear_button.grid_remove()

    def _load_sessions(self) -> None:
        for child in self.history_box.winfo_children():
            child.destroy()

        try:
            sessions = list_recent_sessions(limit=8)
        except Exception:
            sessions = []

        if not sessions:
            ctk.CTkLabel(self.history_box, text="No saved sessions yet.", text_color="#667085").pack(
                anchor="w",
                padx=8,
                pady=8,
            )
            return

        for session in sessions:
            build_session_history_card(self, session)

    def _style_history_card(self, card: ctk.CTkFrame, session_id: int) -> None:
        if session_id == self.selected_session_id:
            card.configure(fg_color="#dceee3", border_color="#246b45")
        else:
            card.configure(fg_color="#ffffff", border_color="#d8e1d9")

    def _load_session_output(self, session_id: int) -> None:
        self._reset_elapsed_timer()
        detail = load_session_detail(session_id)
        if detail is None:
            self.status_label.configure(text=f"Session #{session_id} was not found.", text_color="#a8071a")
            return

        self.selected_session_id = session_id
        session = detail.get("session", {})
        coordinator = detail.get("coordinator", {})
        nutrition = detail.get("nutrition", {})

        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", session.get("user_input", ""))

        self.age_entry.delete(0, "end")
        self.age_entry.insert(0, str(session.get("age") or 0))
        self.weight_entry.delete(0, "end")
        self.weight_entry.insert(0, str(session.get("weight") or 0))

        self.request_focus_frame.grid()
        self.metrics_frame.grid()
        self.metric_labels["calories"].configure(text=str(nutrition.get("total_calories", 0)))
        self.metric_labels["protein"].configure(text=str(nutrition.get("protein", 0)))
        self.metric_labels["carbs"].configure(text=str(nutrition.get("carbs", 0)))
        self.metric_labels["fat"].configure(text=str(nutrition.get("fat", 0)))

        self._show_loaded_session_context(session_id, coordinator)
        self._show_loaded_session_output(detail)
        self._refresh_history_selection()

    def _show_loaded_session_context(self, session_id: int, coordinator: dict[str, Any]) -> None:
        hint_parts = []
        goal = coordinator.get("goal")
        diet_type = coordinator.get("diet_type")
        target_calories = coordinator.get("target_calories")
        if goal:
            hint_parts.append(f"Goal: {goal}")
        if diet_type and diet_type != "none":
            hint_parts.append(f"Diet: {diet_type}")
        if target_calories:
            hint_parts.append(f"Target: {target_calories} kcal")

        self.request_hint_label.configure(text=" • ".join(hint_parts) if hint_parts else "Loaded saved meal request.")
        self.status_label.configure(text=f"Viewing saved session #{session_id}", text_color="#246b45")
        self.workflow_label.configure(text="Saved session")
        self.workflow_status.configure(text="This output was loaded from recent sessions.")
        self.progress_bar.set(1)
        configure_workflow_steps(self, ["coordinator", *coordinator.get("steps", [])])
        set_workflow_expanded(self, False)
        self.clear_button.configure(state="normal")
        self.clear_button.grid()

        for stage, title, _caption in get_visible_workflow_stages(self):
            set_stage_state(self, stage, title, "Saved", "done")

    def _show_loaded_session_output(self, detail: dict[str, Any]) -> None:
        final_output = detail.get("final_output", "")
        if final_output:
            show_result_output(self, final_output)
            return
        else:
            meals = detail.get("meals", [])
            if meals:
                output_lines = ["Saved meals", ""]
                for meal in meals:
                    output_lines.append(f"- {meal.get('meal_name', 'Meal')}: {meal.get('description', '')}")
                output = "\n".join(output_lines)
            else:
                output = "This session does not have a saved output yet."

        show_text_output(self, output)

    def _refresh_history_selection(self) -> None:
        for card in self.history_box.winfo_children():
            try:
                title = card.winfo_children()[0]
                title_text = title.cget("text")
                session_id = int(title_text.split()[0].replace("#", ""))
            except (IndexError, ValueError, AttributeError):
                continue
            self._style_history_card(card, session_id)

    @staticmethod
    def _read_int(value: str) -> int:
        try:
            return int(value)
        except ValueError:
            return 0


if __name__ == "__main__":
    app = MealPlannerDesktopApp()
    app.mainloop()
