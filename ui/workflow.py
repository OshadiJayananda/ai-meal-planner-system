"""Workflow UI for agent progress."""

from typing import Any

import customtkinter as ctk


STEP_UI = {
    "coordinator": ("Analyze", "Read request"),
    "meal_generation": ("Generate", "Build meals"),
    "nutrition_analysis": ("Nutrition", "Calculate totals"),
    "format_output": ("Format", "Prepare plan"),
}

WORKFLOW_STAGES = [
    ("coordinator", *STEP_UI["coordinator"]),
    ("meal_generation", *STEP_UI["meal_generation"]),
    ("nutrition_analysis", *STEP_UI["nutrition_analysis"]),
    ("format_output", *STEP_UI["format_output"]),
]

DEFAULT_WORKFLOW_STAGE_KEYS = [stage for stage, _title, _caption in WORKFLOW_STAGES]


def build_workflow(app: Any, parent: ctk.CTkFrame) -> None:
    app.workflow_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
    app.workflow_frame.grid(row=2, column=0, padx=28, pady=(0, 14), sticky="ew")
    app.workflow_frame.grid_columnconfigure(0, weight=1)

    app.workflow_label = ctk.CTkLabel(
        app.workflow_frame,
        text="Agent workflow",
        anchor="w",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color="#21352b",
    )
    app.workflow_label.grid(row=0, column=0, padx=18, pady=(14, 2), sticky="ew")

    app.workflow_status = ctk.CTkLabel(
        app.workflow_frame,
        text="Ready to analyze your meal request.",
        anchor="w",
        text_color="#52615a",
    )
    app.workflow_status.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")

    app.progress_bar = ctk.CTkProgressBar(app.workflow_frame, height=8, corner_radius=999)
    app.progress_bar.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")
    app.progress_bar.set(0)

    app.steps_frame = ctk.CTkFrame(app.workflow_frame, fg_color="transparent")
    app.steps_frame.grid(row=3, column=0, padx=12, pady=(0, 14), sticky="ew")
    configure_workflow_steps(app, DEFAULT_WORKFLOW_STAGE_KEYS)


def configure_workflow_steps(app: Any, stage_keys: list[str] | tuple[str, ...] | None) -> None:
    cleaned_stage_keys = ["coordinator"]
    for stage in stage_keys or DEFAULT_WORKFLOW_STAGE_KEYS:
        if stage in STEP_UI and stage not in cleaned_stage_keys:
            cleaned_stage_keys.append(stage)

    previous_count = max(len(getattr(app, "workflow_stage_keys", [])), 4)
    app.workflow_stage_keys = cleaned_stage_keys
    app.step_labels.clear()
    app.step_caption_labels.clear()

    for child in app.steps_frame.winfo_children():
        child.destroy()

    for column in range(previous_count):
        app.steps_frame.grid_columnconfigure(column, weight=0)
    for column in range(len(cleaned_stage_keys)):
        app.steps_frame.grid_columnconfigure(column, weight=1)

    for column, stage in enumerate(cleaned_stage_keys):
        title, caption = STEP_UI[stage]
        card = ctk.CTkFrame(app.steps_frame, fg_color="#f3f6f3", corner_radius=8)
        card.grid(row=0, column=column, padx=6, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#667085",
            anchor="w",
        )
        title_label.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="ew")

        caption_label = ctk.CTkLabel(card, text=caption, text_color="#7a867e", anchor="w")
        caption_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")

        app.step_labels[stage] = title_label
        app.step_caption_labels[stage] = caption_label


def reset_workflow(app: Any) -> None:
    set_workflow_expanded(app, True)
    app.progress_bar.set(0)
    app.workflow_label.configure(text="Agent workflow")
    app.workflow_status.configure(text="Ready to analyze your meal request.")
    for stage, title, caption in get_visible_workflow_stages(app):
        set_stage_state(app, stage, title, caption, "pending")


def set_workflow_expanded(app: Any, expanded: bool) -> None:
    if expanded:
        app.progress_bar.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")
        app.steps_frame.grid(row=3, column=0, padx=12, pady=(0, 14), sticky="ew")
        app.workflow_frame.grid_configure(pady=(0, 14))
    else:
        app.progress_bar.grid_remove()
        app.steps_frame.grid_remove()
        app.workflow_frame.grid_configure(pady=(0, 10))


def set_stage_state(app: Any, stage: str, title: str, caption: str, state: str) -> None:
    colors = {
        "pending": ("#667085", "#7a867e"),
        "active": ("#246b45", "#246b45"),
        "done": ("#21352b", "#52615a"),
    }
    title_color, caption_color = colors.get(state, colors["pending"])

    if stage in app.step_labels:
        app.step_labels[stage].configure(text=title, text_color=title_color)
    if stage in app.step_caption_labels:
        app.step_caption_labels[stage].configure(text=caption, text_color=caption_color)


def update_workflow_state(app: Any, stage: str, message: str) -> None:
    visible_stages = get_visible_workflow_stages(app)
    stage_order = [stage_key for stage_key, _title, _caption in visible_stages]
    if stage not in stage_order:
        return

    current_index = stage_order.index(stage)
    message_lower = message.lower()
    is_done = any(word in message_lower for word in ("analyzed", "generated", "complete", "formatted"))

    for index, (stage_key, title, caption) in enumerate(visible_stages):
        if index < current_index or (stage_key == stage and is_done):
            set_stage_state(app, stage_key, title, "Done", "done")
        elif stage_key == stage:
            set_stage_state(app, stage_key, title, "In progress", "active")
        else:
            set_stage_state(app, stage_key, title, caption, "pending")

    progress = (current_index + (1 if is_done else 0.45)) / len(visible_stages)
    app.progress_bar.set(min(progress, 1))


def get_visible_workflow_stages(app: Any) -> list[tuple[str, str, str]]:
    stage_keys = getattr(app, "workflow_stage_keys", DEFAULT_WORKFLOW_STAGE_KEYS)
    return [(stage, *STEP_UI[stage]) for stage in stage_keys if stage in STEP_UI]
