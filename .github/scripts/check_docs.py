#!/usr/bin/env python3
"""Check that DATASETS.md and the README describe everything the published data holds.

1. Every dataset in data/index.json has a heading in DATASETS.md and a row in the README's
   Datasets table (a per-language dataset written `<name>.<locale>`).
2. Every field name in the published files and data/index.json appears in backticks in
   DATASETS.md.

Documenting ahead of the data is fine, so only what the docs lack is reported. Exits 1 when
something is missing. With --report FILE, also writes the gaps as Markdown for an issue.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# Maps keyed by a name rather than a field: their keys are skipped. Each is the field holding the
# map, with `[*]` for each value key between it and the names.
NAME_KEYED = {
    "rep",  # creatures: rep["<race>"][factionId][change]
    "zones[*]",  # game_rules: zones[locale]["<zone text>"]
    "subZones[*]",  # game_rules: subZones[locale]["<subzone text>"]
}

LOCALE = re.compile(r"^[a-z]{2}[A-Z]{2}$")
NUMBER = re.compile(r"^-?\d+(\.\d+)?$")
ALL_CAPS = re.compile(r"^[A-Z][A-Z0-9_]*$")
RANGE = re.compile(r"^-?\d+\.\.-?\d+$")  # game_rules standings: "0..3000"


def is_value_key(key):
    """A key that is a value (an ID, a locale, a game key) rather than a field name."""
    return (
        key == "?"
        or NUMBER.match(key) is not None
        or RANGE.match(key) is not None
        or LOCALE.match(key) is not None
        or ALL_CAPS.match(key) is not None
        or any(c in key for c in ":>|")
    )


def dataset_name(stem):
    """`texts.enUS` -> `texts.<locale>`."""
    name, _, locale = stem.partition(".")
    return f"{name}.<locale>" if locale else name


def walk(node, path, parent, out):
    """Collect (field path, key) for every field key under node.

    parent is the nearest field above node, with `[*]` for each value key since.
    """
    if isinstance(node, list):
        for item in node:
            walk(item, path + "[]", parent, out)
    elif isinstance(node, dict):
        for key, value in node.items():
            if parent in NAME_KEYED or is_value_key(key):
                walk(value, path + "[*]", parent and parent + "[*]", out)
            else:
                sub = f"{path}.{key}" if path else key
                out.add((sub, key))
                walk(value, sub, key, out)


def documented_words(text):
    """Every identifier inside a backtick span of the Markdown, fenced code blocks left out."""
    text = re.sub(r"^```.*?^```[^\n]*$", "", text, flags=re.S | re.M)
    words = set()
    for span in re.findall(r"`([^`\n]+)`", text):
        words.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", html.unescape(span)))
    return words


def headings(text):
    return [html.unescape(line) for line in text.splitlines() if re.match(r"#{2,6} ", line)]


def readme_rows(text):
    return {m.group(1) for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|", text, flags=re.M)}


def check():
    datasets_md = (ROOT / "DATASETS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    words = documented_words(datasets_md)
    heads = headings(datasets_md)
    rows = readme_rows(readme)

    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    builds_of = {}  # dataset -> builds it is in
    for product, builds in index["products"].items():
        for build, datasets in builds.items():
            for stem in datasets:
                builds_of.setdefault(dataset_name(stem), set()).add(build)

    gaps = []  # (dataset, what is missing, builds)
    for dataset in sorted(builds_of):
        builds = builds_of[dataset]
        pattern = re.compile(rf"(?<![\w.]){re.escape(dataset)}(?![\w.<])")
        if not any(pattern.search(h) for h in heads):
            gaps.append((dataset, "no heading in DATASETS.md", builds))
        if dataset not in rows:
            gaps.append((dataset, "no row in the README's Datasets table", builds))

    # Field paths per dataset, with the builds each is in.
    fields = {}  # (dataset, path, key) -> builds
    index_fields = set()
    for key, value in index.items():
        if key != "products":
            walk(value, key, key, index_fields)
            index_fields.add((key, key))
    for builds in index["products"].values():
        for datasets in builds.values():
            for counts in datasets.values():
                walk(counts, "products[*][*][*]", None, index_fields)
    index_fields.add(("products", "products"))
    for path, key in index_fields:
        fields.setdefault(("index.json", path, key), set())

    for file in sorted(DATA.glob("*/*/*.json")):
        build = file.parent.name
        found = set()
        walk(json.loads(file.read_text(encoding="utf-8")), "", None, found)
        for path, key in found:
            fields.setdefault((dataset_name(file.stem), path, key), set()).add(build)

    for (dataset, path, key), builds in sorted(fields.items()):
        if key not in words:
            gaps.append((dataset, f"field `{path}`", builds))
    return gaps


def build_list(builds):
    return ", ".join(sorted(builds)) if builds else "-"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, help="write the gaps as Markdown to this file")
    args = parser.parse_args()

    gaps = check()
    if not gaps:
        print("DATASETS.md and the README describe every dataset and field.")
        return 0

    print(f"{len(gaps)} gap(s) in the docs:")
    for dataset, what, builds in gaps:
        print(f"  {dataset}: {what.replace('`', '')} [{build_list(builds)}]")

    if args.report:
        lines = [
            "The published data has datasets or fields that `DATASETS.md` (or the README's "
            "Datasets table) doesn't describe. Describe them, and the docs check closes this "
            "issue on its next pass.",
            "",
            "| Dataset | Missing | Builds |",
            "|---|---|---|",
        ]
        lines += [f"| `{d}` | {w} | {build_list(b)} |" for d, w, b in gaps]
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1


if __name__ == "__main__":
    sys.exit(main())
