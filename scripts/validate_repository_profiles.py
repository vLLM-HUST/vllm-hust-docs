#!/usr/bin/env python3
"""Validate repository-local profiles against schema and canonical portfolio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "registry" / "repository-profile.schema.json"
PORTFOLIO = ROOT / "registry" / "repository-portfolio.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("profiles", nargs="+", type=Path)
    parser.add_argument("--require-complete-portfolio", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    portfolio = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
    repositories = {
        repository["url"]: repository for repository in portfolio["repositories"]
    }
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    seen: dict[str, Path] = {}
    for path in args.profiles:
        profile = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(
            validator.iter_errors(profile), key=lambda error: list(error.path)
        )
        if errors:
            formatted = "; ".join(
                f"{'.'.join(str(item) for item in error.path) or '<root>'}: "
                f"{error.message}"
                for error in errors
            )
            raise SystemExit(f"{path}: {formatted}")

        repository_url = profile["repository"]
        if repository_url in seen:
            raise SystemExit(
                f"duplicate profile for {repository_url}: {seen[repository_url]} and {path}"
            )
        seen[repository_url] = path

        canonical = repositories.get(repository_url)
        if canonical is None:
            raise SystemExit(f"{path}: repository is absent from canonical portfolio")
        for field in ("repository_role", "relation_to_runtime", "lifecycle"):
            if profile[field] != canonical[field]:
                raise SystemExit(
                    f"{path}: {field}={profile[field]!r} differs from "
                    f"portfolio value {canonical[field]!r}"
                )

        artifact_ids = [artifact["id"] for artifact in profile["artifacts"]]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise SystemExit(f"{path}: artifact ids must be unique")

    if args.require_complete_portfolio:
        missing = sorted(set(repositories) - set(seen))
        extra = sorted(set(seen) - set(repositories))
        if missing or extra:
            raise SystemExit(
                f"profile coverage mismatch: missing={missing}, extra={extra}"
            )

    print(
        f"validated {len(seen)} repository profiles"
        + (
            " with complete portfolio coverage"
            if args.require_complete_portfolio
            else ""
        )
    )


if __name__ == "__main__":
    main()
