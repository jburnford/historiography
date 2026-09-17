#!/usr/bin/env python3
"""Build the Field-view prototype into prototype/dist.

Mirrors scripts/build_site.py discipline: an explicit allowlist, its own output
directory, and no path that would expose the repository root (which holds the
local OpenAlex key). Serve prototype/dist, never the repository root.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "prototype"
DIST = SRC / "dist"
PAGE_FILES = ["index.html", "styles.css", "field.js"]
DATA_FILES = {"graph.json": "historiography-1920-2000.json",
              "pathways.json": "seminar-pathways.json"}


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "data").mkdir(parents=True)
    for name in PAGE_FILES:
        shutil.copy2(SRC / name, DIST / name)
    for out_name, src_name in DATA_FILES.items():
        payload = json.loads((ROOT / src_name).read_text(encoding="utf-8"))
        (DIST / "data" / out_name).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    graph = json.loads((DIST / "data" / "graph.json").read_text(encoding="utf-8"))
    print(f"Built {len(PAGE_FILES) + len(DATA_FILES)} files in {DIST}")
    print(f"  {len(graph['nodes'])} entries, {len(graph['edges'])} relationships, "
          f"revision {graph['revision_history'][-1]['version']}")


if __name__ == "__main__":
    main()
