#!/usr/bin/env python3
"""
generate-xmind.py
Packages a content.xml into a valid XMind 8 (.xmind) file.

Usage:
    python3 generate-xmind.py <content_xml_path> <output_title> [--figma-nodes <file_key>:<node_ids>]

Example:
    python3 generate-xmind.py /tmp/qa_tc_content.xml "Checkout Flow Test Cases"
    python3 generate-xmind.py /tmp/qa_tc_content.xml "Checkout Flow Test Cases" --figma-nodes abc123:1-2,1-3
"""

import argparse
import os
import sys
import zipfile
import re
import urllib.request
import urllib.error
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


def sanitize_filename(name: str) -> str:
    """Remove characters not suitable for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def fetch_figma_images(file_key: str, node_ids: list[str], token: str) -> dict[str, bytes]:
    """
    Fetch PNG exports from Figma API.
    Returns dict of {node_id: image_bytes}.
    Skips nodes that fail silently.
    """
    ids_param = ",".join(node_ids)
    url = f"https://api.figma.com/v1/images/{file_key}?ids={ids_param}&format=png&scale=2"

    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = __import__("json").loads(resp.read())
    except urllib.error.URLError as e:
        print(f"[Figma] Failed to fetch image list: {e}", file=sys.stderr)
        return {}

    images = {}
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


def build_xmind(content_xml_path: str, output_path: str, figma_images: dict[str, bytes]) -> None:
    """Create the .xmind zip file."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Main mind map content
        zf.write(content_xml_path, "content.xml")

        # Metadata
        zf.writestr("META-INF/manifest.xml", MANIFEST_XML)
        zf.writestr("metadata.xml", METADATA_XML)

        # Figma images as attachments
        for node_id, img_bytes in figma_images.items():
            safe_id = node_id.replace(":", "_").replace(",", "_")
            attachment_path = f"attachments/figma_{safe_id}.png"
            zf.writestr(attachment_path, img_bytes)
            print(f"[XMind] Embedded image: {attachment_path}")


def main():
    parser = argparse.ArgumentParser(description="Package content.xml into XMind 8 format")
    parser.add_argument("content_xml", help="Path to content.xml")
    parser.add_argument("output_title", help="Output filename (without .xmind extension)")
    parser.add_argument(
        "--figma-nodes",
        help="Figma nodes to embed: <file_key>:<node_id1>,<node_id2>",
        default=None,
    )
    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.content_xml):
        print(f"Error: content.xml not found at {args.content_xml}", file=sys.stderr)
        sys.exit(1)

    # Resolve output path
    desktop = Path.home() / "Desktop"
    safe_title = sanitize_filename(args.output_title)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = desktop / f"{safe_title}_{timestamp}.xmind"

    # Fetch Figma images if requested
    figma_images = {}
    if args.figma_nodes:
        token = os.environ.get("FIGMA_TOKEN")
        if not token:
            print(
                "[Figma] FIGMA_TOKEN environment variable not set. Skipping image embedding.",
                file=sys.stderr,
            )
        else:
            parts = args.figma_nodes.split(":", 1)
            if len(parts) == 2:
                file_key, node_ids_str = parts
                node_ids = [n.strip() for n in node_ids_str.split(",") if n.strip()]
                figma_images = fetch_figma_images(file_key, node_ids, token)
            else:
                print(
                    f"[Figma] Invalid --figma-nodes format: {args.figma_nodes}. Expected <file_key>:<node_ids>",
                    file=sys.stderr,
                )

    # Build the file
    build_xmind(args.content_xml, str(output_path), figma_images)
    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
