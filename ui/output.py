"""Main request, metrics, and output panels."""

import re
from typing import Any

import customtkinter as ctk


def build_result_area(app: Any, sample_prompt: str) -> None:
    app.content = ctk.CTkFrame(app, fg_color="#f7faf7", corner_radius=0)
    app.content.grid(row=0, column=1, sticky="nsew")
    app.content.grid_columnconfigure(0, weight=1)
    app.content.grid_rowconfigure(3, weight=5, minsize=360)

    build_request_card(app, app.content, sample_prompt)
    build_metrics(app, app.content)


def build_request_card(app: Any, parent: ctk.CTkFrame, sample_prompt: str) -> None:
    app.request_focus_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
    app.request_focus_frame.grid(row=0, column=0, padx=28, pady=(28, 14), sticky="ew")
    app.request_focus_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        app.request_focus_frame,
        text="Ready to build your meal plan",
        text_color="#246b45",
        font=ctk.CTkFont(size=15, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, padx=18, pady=(16, 2), sticky="ew")

    ctk.CTkLabel(
        app.request_focus_frame,
        text="Enter what you want to eat, your goal, or the meals you want analyzed.",
        font=ctk.CTkFont(size=20, weight="bold"),
        anchor="w",
        wraplength=720,
        justify="left",
    ).grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")

    app.prompt_text = ctk.CTkTextbox(
        app.request_focus_frame,
        height=96,
        wrap="word",
        fg_color="#fbfcfb",
        border_width=1,
        border_color="#d8e1d9",
        corner_radius=8,
    )
    app.prompt_text.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="ew")
    app.prompt_text.insert("1.0", sample_prompt)
    app.prompt_text.bind("<KeyRelease>", app._sync_request_preview)

    app.request_hint_label = ctk.CTkLabel(
        app.request_focus_frame,
        text="Pick a sample prompt from the sidebar or write your own request here.",
        text_color="#334139",
        anchor="w",
        justify="left",
        wraplength=720,
    )
    app.request_hint_label.grid(row=3, column=0, padx=18, pady=(0, 18), sticky="ew")


def build_metrics(app: Any, parent: ctk.CTkFrame) -> None:
    app.metrics_frame = ctk.CTkFrame(parent, fg_color="transparent")
    app.metrics_frame.grid(row=1, column=0, padx=28, pady=(0, 14), sticky="ew")
    app.metrics_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    app.metric_labels = {
        "calories": build_metric_card(app.metrics_frame, "Calories", "0", "kcal", 0),
        "protein": build_metric_card(app.metrics_frame, "Protein", "0", "g", 1),
        "carbs": build_metric_card(app.metrics_frame, "Carbs", "0", "g", 2),
        "fat": build_metric_card(app.metrics_frame, "Fat", "0", "g", 3),
    }
    app.metrics_frame.grid_remove()


def build_metric_card(parent: ctk.CTkFrame, title: str, value: str, suffix: str, column: int) -> ctk.CTkLabel:
    card = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
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


def build_output_panel(app: Any, parent: ctk.CTkFrame) -> None:
    app.output_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
    app.output_frame.grid(row=3, column=0, padx=28, pady=(0, 28), sticky="nsew")
    app.output_frame.grid_columnconfigure(0, weight=1)
    app.output_frame.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(
        app.output_frame,
        text="Planner output",
        font=ctk.CTkFont(size=15, weight="bold"),
        anchor="w",
        text_color="#21352b",
    ).grid(row=0, column=0, padx=18, pady=(14, 8), sticky="ew")

    app.output_table_frame = ctk.CTkScrollableFrame(
        app.output_frame,
        fg_color="#fbfcfb",
        border_width=1,
        border_color="#e3e9e3",
        corner_radius=8,
    )
    app.output_table_frame.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
    app.output_table_frame.grid_remove()

    app.output_text = ctk.CTkTextbox(
        app.output_frame,
        wrap="word",
        font=ctk.CTkFont(size=14),
        height=360,
        fg_color="#fbfcfb",
        border_width=1,
        border_color="#e3e9e3",
        corner_radius=8,
    )
    app.output_text.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
    app.output_text.insert("1.0", "Your meal plan will appear here after you generate a request.")


def show_text_output(app: Any, text: str) -> None:
    app.output_table_frame.grid_remove()
    _clear_children(app.output_table_frame)
    app.output_text.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
    app.output_text.delete("1.0", "end")
    app.output_text.insert("1.0", text)


def show_result_output(app: Any, output: str) -> None:
    rows = parse_markdown_table(output)
    if rows:
        app.output_text.grid_remove()
        _clear_children(app.output_table_frame)
        app.output_table_frame.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        render_mixed_output_ui(app.output_table_frame, output, rows)
        return

    show_text_output(app, format_output_for_display(output))


def format_output_for_display(output: str) -> str:
    """Convert simple Markdown-style model output into cleaner textbox text."""
    if not output:
        return ""

    cleaned_lines: list[str] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()

        if not line:
            cleaned_lines.append("")
            continue

        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"^\*\s+", "  o ", line)
        line = re.sub(r"^-\s+", "  o ", line)
        line = re.sub(r"^\d+\.\s+", "  o ", line)

        if _looks_like_heading(line):
            cleaned_lines.append("")
            cleaned_lines.append(line.upper())
            cleaned_lines.append("")
        else:
            cleaned_lines.append(line)

    return _collapse_blank_lines("\n".join(cleaned_lines)).strip()


def parse_markdown_table(output_text: str) -> list[dict[str, str]]:
    """Parse the first Markdown table in a model output into row dictionaries."""
    table_lines = [line.strip() for line in output_text.splitlines() if _is_table_line(line)]
    if len(table_lines) < 3:
        return []

    for index in range(len(table_lines) - 2):
        header_line = table_lines[index]
        separator_line = table_lines[index + 1]
        if not _is_separator_line(separator_line):
            continue

        headers = _split_table_row(header_line)
        if not headers:
            continue

        rows: list[dict[str, str]] = []
        for row_line in table_lines[index + 2:]:
            if _is_separator_line(row_line):
                continue
            values = _split_table_row(row_line)
            if len(values) != len(headers):
                break
            rows.append(dict(zip(headers, values)))

        if rows:
            return rows

    return []


def render_table_ui(parent: ctk.CTkFrame, rows: list[dict[str, str]]) -> None:
    if not rows:
        return

    headers = list(rows[0].keys())

    for i in range(len(headers)):
        parent.grid_columnconfigure(i, weight=1)

    for col, header in enumerate(headers):
        ctk.CTkLabel(
            parent,
            text=header,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#dceee3",
            corner_radius=5,
            anchor="w",
        ).grid(row=0, column=col, padx=5, pady=5, sticky="ew")

    for row_index, row_data in enumerate(rows, start=1):
        for col, header in enumerate(headers):
            ctk.CTkLabel(
                parent,
                text=row_data.get(header, ""),
                fg_color="#f8faf8",
                corner_radius=5,
                anchor="w",
                justify="left",
                wraplength=220,
            ).grid(row=row_index, column=col, padx=5, pady=5, sticky="nsew")


def render_mixed_output_ui(parent: ctk.CTkFrame, output: str, rows: list[dict[str, str]]) -> None:
    parent.grid_columnconfigure(0, weight=1)

    text_without_tables = format_output_for_display(_remove_markdown_tables(output))
    if text_without_tables:
        ctk.CTkLabel(
            parent,
            text=text_without_tables,
            anchor="w",
            justify="left",
            wraplength=1180,
            text_color="#21352b",
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")

    table_wrapper = ctk.CTkFrame(parent, fg_color="transparent")
    table_wrapper.grid(row=1, column=0, padx=10, pady=(4, 12), sticky="ew")
    table_wrapper.grid_columnconfigure(0, weight=1)
    render_table_ui(table_wrapper, rows)


def _looks_like_heading(line: str) -> bool:
    return (
        not line.startswith("  o ")
        and len(line.split()) <= 4
        and line[0].isupper()
        and not line.endswith(".")
        and "|" not in line
    )


def _collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _clear_children(parent: ctk.CTkFrame) -> None:
    for child in parent.winfo_children():
        child.destroy()


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _is_separator_line(line: str) -> bool:
    cells = _split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _remove_markdown_tables(output_text: str) -> str:
    kept_lines: list[str] = []
    in_table = False

    for line in output_text.splitlines():
        if _is_table_line(line):
            in_table = True
            continue

        if in_table:
            kept_lines.append("")
            in_table = False

        kept_lines.append(line)

    return "\n".join(kept_lines)
