from __future__ import annotations

import base64
import json

from nicegui import ui


OSMD_JS_URL = "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"


def load_notation_script() -> None:
    ui.add_body_html(f'<script src="{OSMD_JS_URL}"></script>')


def render_musicxml(musicxml: str, container_id: str) -> None:
    if not musicxml:
        return
    ui.element("div").props(f'id={container_id} data-testid={container_id}').classes("w-full overflow-x-auto min-h-32")
    encoded = base64.b64encode(musicxml.encode("utf-8")).decode("ascii")
    ui.run_javascript(f"""
        (async () => {{
            const container = document.getElementById({json.dumps(container_id)});
            if (!container) return;
            try {{
                for (let attempt = 0; !window.opensheetmusicdisplay && attempt < 100; attempt++) {{
                    await new Promise(resolve => setTimeout(resolve, 100));
                }}
                if (!window.opensheetmusicdisplay) throw new Error('Notation library did not load. Check the connection and reload.');
                if (!container.isConnected) return;
                const bytes = Uint8Array.from(atob({json.dumps(encoded)}), c => c.charCodeAt(0));
                const xml = new TextDecoder().decode(bytes);
                const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(container, {{
                    autoResize: true, backend: 'svg', drawTitle: false,
                    drawSubtitle: false, drawComposer: false,
                }});
                await osmd.load(xml);
                if (container.isConnected) osmd.render();
            }} catch (error) {{
                container.textContent = 'Notation unavailable: ' + error.message;
                container.dataset.renderError = 'true';
            }}
        }})();
    """)
