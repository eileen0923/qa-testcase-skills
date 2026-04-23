#!/usr/bin/env python3
"""
generate-xmind.py
Converts a compact TC text file OR an existing content.xml into a valid XMind 8 (.xmind) file.

Compact format (.txt):
    MODULE: {module name}
    TC: {title} | {P0-P3} | {FE/BE/BE2}
    PRE: {pre-condition}   (optional)
    1. {step}
    2. {step}
    > {expected result}
    > {more ER lines}
    3. {pure op step}      (no > = no ER = childless node)
    ---                    (optional separator, ignored)

Usage:
    python3 generate-xmind.py <input_file> <output_title> [--figma-nodes <file_key>:<node_ids>]

    Input can be .txt (compact format) or .xml (XMind XML, embedded as-is).
"""

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path


MANIFEST_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
  <file-entry full-path="content.xml" media-type="text/xml"/>
  <file-entry full-path="META-INF/" media-type=""/>
  <file-entry full-path="META-INF/manifest.xml" media-type="text/xml"/>
</manifest>"""

METADATA_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" AdaptTo="xmind-zen" IsFlat="false"/>"""

PRIORITY_MAP = {"P0": "priority-1", "P1": "priority-2", "P2": "priority-3", "P3": "priority-4"}
PLATFORM_MAP = {"FE": "FE (Web/mWeb/Android/iOS)", "BE": "BE", "BE2": "BE2"}


# ── Compact format parser ──────────────────────────────────────────────────────

def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def parse_compact(text: str) -> list[dict]:
    """
    Returns list of modules:
        [{'name': str, 'tcs': [{'title', 'priority', 'platform', 'pre', 'groups'}]}]
    Each group: (steps_text: str, er_text: str | None)
    """
    modules: list[dict] = []
    cur_module: dict | None = None
    cur_tc: dict | None = None
    pending_steps: list[str] = []
    pending_er: list[str] = []
    in_er = False

    def flush_group():
        nonlocal pending_steps, pending_er, in_er
        if pending_steps or pending_er:
            steps_text = "\n".join(pending_steps)
            er_text = "\n".join(pending_er) if pending_er else None
            if cur_tc is not None:
                cur_tc["groups"].append((steps_text, er_text))
        pending_steps.clear()
        pending_er.clear()
        in_er = False

    def flush_tc():
        nonlocal cur_tc
        if cur_tc is not None:
            flush_group()
            if cur_module is not None:
                cur_module["tcs"].append(cur_tc)
            cur_tc = None

    def flush_module():
        nonlocal cur_module
        if cur_module is not None:
            flush_tc()
            modules.append(cur_module)
            cur_module = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.strip() == "---":
            continue

        if line.startswith("MODULE:"):
            flush_module()
            cur_module = {"name": line[7:].strip(), "tcs": []}

        elif line.startswith("TC:"):
            flush_tc()
            parts = [p.strip() for p in line[3:].split("|")]
            priority = parts[1].upper() if len(parts) > 1 else "P1"
            platform_key = parts[2].upper() if len(parts) > 2 else "FE"
            platform = PLATFORM_MAP.get(platform_key, parts[2].strip() if len(parts) > 2 else "FE (Web/mWeb/Android/iOS)")
            cur_tc = {
                "title": parts[0],
                "priority": priority,
                "platform": platform,
                "pre": None,
                "groups": [],
            }

        elif line.startswith("PRE:"):
            if cur_tc is not None:
                extra = line[4:].strip()
                cur_tc["pre"] = (cur_tc["pre"] + "\n" + extra) if cur_tc["pre"] else extra

        elif line.lstrip().startswith(">"):
            er_line = line.lstrip()[1:].strip()
            in_er = True
            pending_er.append(er_line)

        elif re.match(r"^\s*\d+\.", line):
            if in_er:
                flush_group()
            pending_steps.append(line.strip())

        else:
            # Continuation of last step or ER
            if in_er:
                pending_er.append(line.strip())
            elif pending_steps:
                pending_steps[-1] += " " + line.strip()

    flush_module()
    return modules


# ── XML generator ──────────────────────────────────────────────────────────────

def generate_xml(modules: list[dict], prd_title: str) -> str:
    ts = str(int(datetime.now().timestamp() * 1000))
    out: list[str] = []

    out.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    out.append('<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0"')
    out.append('              xmlns:xlink="http://www.w3.org/1999/xlink"')
    out.append(f'              timestamp="{ts}" version="2.0">')
    out.append(f'  <sheet id="sheet-1" timestamp="{ts}">')
    out.append(f'    <topic id="root" timestamp="{ts}">')
    out.append(f'      <title>{escape_xml(prd_title)}</title>')
    out.append('      <children><topics type="attached">')

    for mi, module in enumerate(modules, 1):
        mid = f"m{mi}"
        out.append(f'        <topic id="{mid}" timestamp="{ts}">')
        out.append(f'          <title>{escape_xml(module["name"])}</title>')
        if not module["tcs"]:
            out.append(f'        </topic>')
            continue
        out.append('          <children><topics type="attached">')

        for si, tc in enumerate(module["tcs"], 1):
            sid = f"{mid}-s{si}"
            marker = PRIORITY_MAP.get(tc["priority"], "priority-2")
            out.append(f'            <topic id="{sid}" timestamp="{ts}">')
            out.append(f'              <title>{escape_xml(tc["title"])}</title>')
            out.append(f'              <labels><label>{escape_xml(tc["platform"])}</label></labels>')
            out.append(f'              <marker-refs><marker-ref marker-id="{marker}"/></marker-refs>')
            if not tc["groups"]:
                out.append(f'            </topic>')
                continue
            out.append('              <children><topics type="attached">')

            for gi, (steps_text, er_text) in enumerate(tc["groups"], 1):
                gid = f"{sid}-g{gi}"
                node_text = steps_text
                if gi == 1 and tc["pre"]:
                    node_text = f'Pre-condition:\n{tc["pre"]}\n\nSteps:\n{steps_text}'

                if er_text:
                    out.append(f'                <topic id="{gid}" timestamp="{ts}">')
                    out.append(f'                  <title>{escape_xml(node_text)}</title>')
                    out.append('                  <children><topics type="attached">')
                    out.append(f'                    <topic id="{gid}-er" timestamp="{ts}">')
                    out.append(f'                      <title>{escape_xml(er_text)}</title>')
                    out.append('                    </topic>')
                    out.append('                  </topics></children>')
                    out.append('                </topic>')
                else:
                    out.append(f'                <topic id="{gid}" timestamp="{ts}">')
                    out.append(f'                  <title>{escape_xml(node_text)}</title>')
                    out.append('                </topic>')

            out.append('              </topics></children>')
            out.append('            </topic>')

        out.append('          </topics></children>')
        out.append('        </topic>')

    out.append('      </topics></children>')
    out.append('    </topic>')
    out.append('    <title>Test Cases</title>')
    out.append('  </sheet>')
    out.append('</xmap-content>')

    return "\n".join(out)


# ── Figma ──────────────────────────────────────────────────────────────────────

def fetch_figma_images(file_key: str, node_ids: list[str], token: str) -> dict[str, bytes]:
    ids_param = ",".join(node_ids)
    url = f"https://api.figma.com/v1/images/{file_key}?ids={ids_param}&format=png&scale=2"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = __import__("json").loads(resp.read())
    except urllib.error.URLError as e:
        print(f"[Figma] Failed to fetch image list: {e}", file=sys.stderr)
        return {}

    images: dict[str, bytes] = {}
    for node_id, img_url in (data.get("images") or {}).items():
        if not img_url:
            print(f"[Figma] No export URL for node {node_id}, skipping.", file=sys.stderr)
            continue
        try:
            with urllib.request.urlopen(img_url, timeout=30) as r:
                images[node_id] = r.read()
                print(f"[Figma] Downloaded image for node {node_id} ({len(images[node_id])} bytes)")
        except urllib.error.URLError as e:
            print(f"[Figma] Failed to download image for node {node_id}: {e}", file=sys.stderr)
    return images


# ── Packaging ──────────────────────────────────────────────────────────────────

def build_xmind(xml_content: str, output_path: str, figma_images: dict[str, bytes]) -> None:
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("content.xml", xml_content.encode("utf-8"))
        zf.writestr("META-INF/manifest.xml", MANIFEST_XML)
        zf.writestr("metadata.xml", METADATA_XML)
        for node_id, img_bytes in figma_images.items():
            safe_id = node_id.replace(":", "_").replace(",", "_")
            attachment_path = f"attachments/figma_{safe_id}.png"
            zf.writestr(attachment_path, img_bytes)
            print(f"[XMind] Embedded image: {attachment_path}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Convert compact TC text or content.xml to XMind 8")
    parser.add_argument("input_file", help="Path to compact .txt or content.xml")
    parser.add_argument("output_title", help="Output filename (without .xmind)")
    parser.add_argument("--figma-nodes", help="Figma nodes: <file_key>:<node_id1>,<node_id2>", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    desktop = Path.home() / "Desktop"
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", args.output_title).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = desktop / f"{safe_title}_{timestamp}.xmind"

    figma_images: dict[str, bytes] = {}
    if args.figma_nodes:
        token = os.environ.get("FIGMA_TOKEN")
        if not token:
            print("[Figma] FIGMA_TOKEN not set. Skipping image embedding.", file=sys.stderr)
        else:
            parts = args.figma_nodes.split(":", 1)
            if len(parts) == 2:
                file_key, node_ids_str = parts
                node_ids = [n.strip() for n in node_ids_str.split(",") if n.strip()]
                figma_images = fetch_figma_images(file_key, node_ids, token)
            else:
                print(f"[Figma] Invalid --figma-nodes format: {args.figma_nodes}", file=sys.stderr)

    with open(args.input_file, "r", encoding="utf-8") as f:
        content = f.read()

    if args.input_file.endswith(".xml"):
        xml_content = content
    else:
        modules = parse_compact(content)
        xml_content = generate_xml(modules, args.output_title)

    build_xmind(xml_content, str(output_path), figma_images)
    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
