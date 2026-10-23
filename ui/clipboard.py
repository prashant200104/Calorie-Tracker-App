"""A real copy-to-clipboard button. Streamlit has no native one.

It lives in its own iframe (`components.html`), so the ids and styles here
cannot collide with the page or with a second button beside it.
"""

import json

import streamlit.components.v1 as components


def copy_button(text, label="Copy", height=46):
    """navigator.clipboard needs a secure context, so a hidden-textarea
    execCommand fallback keeps it working over plain http on the LAN."""
    payload = json.dumps(text)
    label_json = json.dumps(label)
    components.html(
        f"""
<style>
  :root {{ color-scheme: light dark; }}
  html, body {{ margin: 0; }}
  button {{
    width: 100%;
    padding: .55rem .75rem;
    font: 600 .9rem/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #fff;
    background: #10b981;
    border: 0;
    border-radius: .5rem;
    cursor: pointer;
  }}
  button:active {{ opacity: .85; }}
  button.done {{ background: #059669; }}
</style>
<button id="ct-copy"></button>
<script>
  const text = {payload};
  const label = {label_json};
  const button = document.getElementById("ct-copy");
  button.textContent = label;

  function fallback() {{
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try {{ ok = document.execCommand("copy"); }} catch (e) {{ ok = false; }}
    document.body.removeChild(area);
    return ok;
  }}

  function done(ok) {{
    button.textContent = ok ? "Copied ✓" : "Press ⌘/Ctrl+C";
    button.classList.toggle("done", ok);
    if (!ok) fallback();
    setTimeout(() => {{
      button.textContent = label;
      button.classList.remove("done");
    }}, 2000);
  }}

  button.addEventListener("click", () => {{
    if (navigator.clipboard && window.isSecureContext) {{
      navigator.clipboard.writeText(text).then(() => done(true), () => done(fallback()));
    }} else {{
      done(fallback());
    }}
  }});
</script>
""",
        height=height,
    )
