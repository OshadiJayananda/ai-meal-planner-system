"""Sidebar UI for the desktop meal planner."""

import textwrap
from typing import Any

import customtkinter as ctk


def build_labeled_entry(parent: ctk.CTkFrame, label: str, value: str, column: int) -> ctk.CTkEntry:
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=0, column=column, padx=(0, 8) if column == 0 else (8, 0), sticky="ew")
    frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(frame, text=label, anchor="w").grid(row=0, column=0, sticky="ew")
    entry = ctk.CTkEntry(frame)
    entry.grid(row=1, column=0, pady=(6, 0), sticky="ew")
    entry.insert(0, value)
    return entry


def build_sample_prompt_card(app: Any, prompt: str, row: int) -> None:
    card = ctk.CTkFrame(app.sidebar, fg_color="#ffffff", corner_radius=8, border_width=1, border_color="#dbe5dc")
    card.grid(row=row, column=0, padx=24, pady=4, sticky="ew")
    card.grid_columnconfigure(0, weight=1)

    label = ctk.CTkLabel(
        card,
        text=textwrap.shorten(prompt, width=72, placeholder="..."),
        anchor="w",
        justify="left",
        wraplength=330,
        text_color="#21352b",
    )
    label.grid(row=0, column=0, padx=12, pady=10, sticky="ew")

    for widget in (card, label):
        widget.bind("<Button-1>", lambda _event, value=prompt: app._set_prompt(value))
        widget.bind("<Enter>", lambda _event, frame=card: frame.configure(fg_color="#e8f2eb"))
        widget.bind("<Leave>", lambda _event, frame=card: frame.configure(fg_color="#ffffff"))


def build_sidebar(app: Any, sample_prompts: list[str]) -> None:
    app.sidebar = ctk.CTkFrame(app, corner_radius=0, width=420, fg_color="#edf2ee")
    app.sidebar.grid(row=0, column=0, sticky="nsew")
    app.sidebar.grid_propagate(False)
    app.sidebar.grid_columnconfigure(0, weight=1)

    title = ctk.CTkLabel(
        app.sidebar,
        text="AI Meal Planner",
        font=ctk.CTkFont(size=30, weight="bold"),
        anchor="w",
    )
    title.grid(row=0, column=0, padx=24, pady=(28, 4), sticky="ew")

    subtitle = ctk.CTkLabel(
        app.sidebar,
        text="Local multi-agent planner powered by Ollama.",
        text_color="#52615a",
        anchor="w",
    )
    subtitle.grid(row=1, column=0, padx=24, pady=(0, 22), sticky="ew")

    profile_frame = ctk.CTkFrame(app.sidebar, fg_color="transparent")
    profile_frame.grid(row=2, column=0, padx=24, pady=(2, 18), sticky="ew")
    profile_frame.grid_columnconfigure((0, 1), weight=1)

    app.age_entry = build_labeled_entry(profile_frame, "Age", "22", 0)
    app.weight_entry = build_labeled_entry(profile_frame, "Weight kg", "70", 1)

    sample_label = ctk.CTkLabel(app.sidebar, text="Sample prompts", font=ctk.CTkFont(weight="bold"), anchor="w")
    sample_label.grid(row=3, column=0, padx=24, pady=(4, 8), sticky="ew")

    for index, prompt in enumerate(sample_prompts, start=4):
        build_sample_prompt_card(app, prompt, index)

    app.generate_button = ctk.CTkButton(
        app.sidebar,
        text="Generate Meal Plan",
        height=48,
        font=ctk.CTkFont(weight="bold"),
        fg_color="#246b45",
        hover_color="#1d5939",
        command=app._generate_plan,
    )
    app.generate_button.grid(row=7, column=0, padx=24, pady=(18, 8), sticky="ew")

    app.clear_button = ctk.CTkButton(
        app.sidebar,
        text="Clear View",
        height=40,
        font=ctk.CTkFont(weight="bold"),
        fg_color="#ffffff",
        hover_color="#e8f2eb",
        text_color="#246b45",
        border_width=1,
        border_color="#b9d4c3",
        command=app._clear_view,
    )
    app.clear_button.grid(row=8, column=0, padx=24, pady=(0, 10), sticky="ew")
    app.clear_button.grid_remove()

    app.status_label = ctk.CTkLabel(
        app.sidebar,
        text="Ready",
        text_color="#52615a",
        anchor="w",
        wraplength=350,
        justify="left",
    )
    app.status_label.grid(row=9, column=0, padx=24, pady=(0, 14), sticky="ew")

    history_label = ctk.CTkLabel(app.sidebar, text="Recent sessions", font=ctk.CTkFont(weight="bold"), anchor="w")
    history_label.grid(row=10, column=0, padx=24, pady=(8, 8), sticky="ew")

    app.history_box = ctk.CTkScrollableFrame(app.sidebar, height=150, fg_color="#e4ebe5", corner_radius=8)
    app.history_box.grid(row=11, column=0, padx=24, pady=(0, 20), sticky="nsew")
    app.sidebar.grid_rowconfigure(11, weight=1)


def build_session_history_card(app: Any, session: dict[str, Any]) -> None:
    session_id = session["id"]
    goal = session.get("goal") or "meal plan"
    calories = session.get("total_calories")
    calorie_text = f" • {calories} kcal" if calories else ""
    request = textwrap.shorten(session.get("user_input", ""), width=96, placeholder="...")

    card = ctk.CTkFrame(app.history_box, fg_color="#ffffff", corner_radius=8, border_width=1, border_color="#d8e1d9")
    card.pack(fill="x", padx=8, pady=6)
    card.grid_columnconfigure(0, weight=1)

    title = ctk.CTkLabel(
        card,
        text=f"#{session_id}  {goal}{calorie_text}",
        font=ctk.CTkFont(size=13, weight="bold"),
        justify="left",
        anchor="w",
        text_color="#21352b",
    )
    title.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="ew")

    body = ctk.CTkLabel(
        card,
        text=request,
        justify="left",
        anchor="w",
        text_color="#52615a",
        wraplength=330,
    )
    body.grid(row=1, column=0, padx=12, pady=(2, 10), sticky="ew")

    for widget in (card, title, body):
        widget.bind("<Button-1>", lambda _event, value=session_id: app._load_session_output(value))
        widget.bind("<Enter>", lambda _event, frame=card: frame.configure(fg_color="#e8f2eb"))
        widget.bind("<Leave>", lambda _event, frame=card, value=session_id: app._style_history_card(frame, value))

    app._style_history_card(card, session_id)
