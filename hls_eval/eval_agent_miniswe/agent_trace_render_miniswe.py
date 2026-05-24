import trace
from datetime import datetime, timezone
from pathlib import Path
from pyexpat import model
from zoneinfo import ZoneInfo


def render_trace_to_html(trace, model_name=None, provider=None) -> str:
    def escape_html(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def render_markdown_code_blocks(text: str) -> str:
        parts = text.split("```")
        rendered_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                rendered_parts.append(escape_html(part))
            else:
                code_lines = part.splitlines()
                if code_lines:
                    first = code_lines[0].strip()
                    if first and " " not in first and "\t" not in first:
                        code = "\n".join(code_lines[1:])
                        lang = first
                    else:
                        code = part
                        lang = ""
                else:
                    code = ""
                    lang = ""
                class_attr = f' class="language-{escape_html(lang)}"' if lang else ""
                rendered_parts.append(
                    f"<pre><code{class_attr}>{escape_html(code)}</code></pre>"
                )
        return "".join(rendered_parts)

    def format_timestamp_est(ts) -> str:
        try:
            dt = datetime.fromtimestamp(float(ts), tz=ZoneInfo("America/New_York"))
        except (TypeError, ValueError):
            return str(ts)
        return dt.strftime("%H:%M:%S")

    def format_cost(value) -> str:
        if value is None:
            return ""
        try:
            return f"${float(value):.6f}"
        except (TypeError, ValueError):
            return str(value)

    css = """
    :root {
        color-scheme: light;
        --bg: #f5f6f8;
        --panel: #ffffff;
        --ink: #111827;
        --muted: #6b7280;
        --border: #e5e7eb;
        --role-system: #dd2d4a;
        --role-user: #55a630;
        --role-assistant: #2196f3;
        --code-bg: #0f172a;
        --code-ink: #e2e8f0;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0;
        padding: 28px;
        font-family: "Space Grotesk", "Segoe UI", "Helvetica Neue", sans-serif;
        background: linear-gradient(180deg, #f8fafc 0%, var(--bg) 100%);
        color: var(--ink);
    }
    .wrap {
        max-width: 980px;
        margin: 0 auto;
    }
    h1 {
        font-size: 30px;
        font-weight: 600;
        margin: 0 0 10px 0;
        letter-spacing: 0.2px;
    }
    .report-meta {
        margin: 0 0 6px 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--ink);
    }
    .report-meta:last-of-type {
        margin-bottom: 16px;
    }
    .message {
        background: var(--panel);
        border: 1px solid var(--border);
        border-left: 6px solid var(--border);
        border-radius: 0;
        padding: 18px 20px;
        margin: 14px 0;
        box-shadow: none;
    }
    .message-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted);
    }
    .message-header span {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 4px 10px;
        border-radius: 0;
        background: #f3f4f6;
        font-weight: 600;
    }
    .message-body {
        font-size: 15px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .role-system { border-left-color: var(--role-system); }
    .role-user { border-left-color: var(--role-user); }
    .role-assistant { border-left-color: var(--role-assistant); }
    .role-system .message-header span { color: var(--role-system); }
    .role-user .message-header span { color: var(--role-user); }
    .role-assistant .message-header span { color: var(--role-assistant); }
    pre {
        background: var(--code-bg);
        color: var(--code-ink);
        padding: 14px 16px;
        border-radius: 0;
        overflow-x: auto;
        margin: 12px 0;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }
    code {
        font-family: "JetBrains Mono", "SFMono-Regular", Menlo, Consolas, monospace;
        font-size: 13.5px;
    }
    .metadata {
        margin-top: 8px;
        font-size: 12px;
        color: var(--muted);
    }
    """

    model_label = model_name if model_name else "Unknown"
    provider_label = provider if provider else "Unknown"

    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>Agent Execution Trace</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        '<div class="wrap">',
        "<h1>Agent Execution Trace</h1>",
        f'<div class="report-meta">Model: {escape_html(str(model_label))}</div>',
        f'<div class="report-meta">Provider: {escape_html(str(provider_label))}</div>',
    ]

    first_ts = None
    running_tokens = 0
    running_cost = 0.0

    for i, message in enumerate(trace):
        role = str(message.get("role", "unknown"))
        content = message.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content, indent=2)
        timestamp = message.get("timestamp")
        if first_ts is None and timestamp is not None:
            try:
                first_ts = float(timestamp)
            except (TypeError, ValueError):
                first_ts = None
        usage = message.get("extra", {}).get("response", {}).get("usage", {})
        input_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        cost_details = usage.get("cost_details", {})
        input_cost = format_cost(cost_details.get("upstream_inference_prompt_cost"))
        output_cost = format_cost(
            cost_details.get("upstream_inference_completions_cost")
        )
        total_tokens = None
        if input_tokens is not None or output_tokens is not None:
            total_tokens = (input_tokens or 0) + (output_tokens or 0)
            running_tokens += total_tokens
        total_cost_val = 0.0
        if cost_details.get("upstream_inference_prompt_cost") is not None:
            total_cost_val += float(
                cost_details.get("upstream_inference_prompt_cost") or 0.0
            )
        if cost_details.get("upstream_inference_completions_cost") is not None:
            total_cost_val += float(
                cost_details.get("upstream_inference_completions_cost") or 0.0
            )
        if total_cost_val:
            running_cost += total_cost_val
        role_class = f"role-{role}"
        rendered_body = render_markdown_code_blocks(content)
        html_parts.extend(
            [
                f'<div class="message {escape_html(role_class)}">',
                '<div class="message-header">',
                f"<span>Step {i + 1} · {escape_html(role.capitalize())}</span>",
                "</div>",
                f'<div class="message-body">{rendered_body}</div>',
            ]
        )
        metadata_bits = []
        if timestamp is not None:
            metadata_bits.append(
                f"Timestamp (EST): {escape_html(format_timestamp_est(timestamp))}"
            )
            if first_ts is not None:
                try:
                    elapsed = max(0, float(timestamp) - first_ts)
                    elapsed_seconds = int(round(elapsed))
                    elapsed_str = str(
                        datetime.fromtimestamp(elapsed_seconds, tz=timezone.utc).time()
                    )
                    metadata_bits.append(f"Elapsed: {escape_html(elapsed_str)}")
                except (TypeError, ValueError):
                    pass
        if input_tokens is not None:
            metadata_bits.append(f"Input tokens: {escape_html(str(input_tokens))}")
        if output_tokens is not None:
            metadata_bits.append(f"Output tokens: {escape_html(str(output_tokens))}")
        if total_tokens is not None:
            metadata_bits.append(f"Total tokens: {escape_html(str(total_tokens))}")
            metadata_bits.append(f"Running tokens: {escape_html(str(running_tokens))}")
        if input_cost:
            metadata_bits.append(f"Input cost: {escape_html(input_cost)}")
        if output_cost:
            metadata_bits.append(f"Output cost: {escape_html(output_cost)}")
        if total_cost_val:
            metadata_bits.append(
                f"Total cost: {escape_html(format_cost(total_cost_val))}"
            )
            metadata_bits.append(
                f"Running cost: {escape_html(format_cost(running_cost))}"
            )
        if metadata_bits:
            html_parts.append(
                f'<div class="metadata">{" · ".join(metadata_bits)}</div>'
            )
        html_parts.append("</div>")

    html_parts.extend(["</div>", "</body>", "</html>"])
    html_content = "".join(html_parts)
    return html_content


if __name__ == "__main__":
    import json

    DIR_CURRENT = Path(__file__).parent.resolve()

    fp_trace = DIR_CURRENT / "test_html_render" / "trace.json"
    trace_data = json.loads(fp_trace.read_text())

    model_name = "openai/gpt-oss-120b"
    provider = "sambanova"

    html_output = render_trace_to_html(trace_data, model_name, provider)

    fp_html = DIR_CURRENT / "test_html_render" / "trace.html"
    fp_html.write_text(html_output)
