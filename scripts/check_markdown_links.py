from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK_RE = re.compile(r'!?\[[^\]]*\]\(([^)\s]+(?:\s+"[^"]*")?)\)')
CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
MARKDOWN_SUFFIXES = {".md", ".markdown"}


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if " \"" in target:
        target = target.split(" \"", 1)[0]
    return target


def should_skip_target(target: str) -> bool:
    if not target or target.startswith("#"):
        return True

    parsed = urlparse(target)
    if parsed.scheme or target.startswith("mailto:"):
        return True
    return False


def target_exists(markdown_file: Path, target: str) -> bool:
    path_part = target.split("#", 1)[0].split("?", 1)[0]
    if not path_part:
        return True

    suffix = Path(unquote(path_part)).suffix.lower()
    if suffix and suffix not in MARKDOWN_SUFFIXES:
        return True

    resolved = (markdown_file.parent / unquote(path_part)).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError:
        return resolved.exists()
    return resolved.exists()


def iter_markdown_files() -> list[Path]:
    return sorted(REPO_ROOT.rglob("*.md"))


def main() -> int:
    markdown_files = iter_markdown_files()
    errors: list[str] = []

    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8")

        for marker in CONFLICT_MARKERS:
            if marker in text:
                errors.append(f"{markdown_file}: found merge conflict marker '{marker}'")

        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in MARKDOWN_LINK_RE.finditer(line):
                target = normalize_target(match.group(1))
                if should_skip_target(target):
                    continue
                if not target_exists(markdown_file, target):
                    errors.append(f"{markdown_file}:{line_number}: missing link target '{target}'")

    if errors:
        print("Markdown validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(markdown_files)} markdown files successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())