#!/usr/bin/env python3
"""Validate cross-repository release-record invariants without extra deps."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "operations" / "ecosystem-reorganization-release-candidate.json"
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def main() -> None:
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    assert record["schema_version"] == "1.0"
    assert record["status"] == "draft"

    repositories = record["repositories"]
    names = [repository["name"] for repository in repositories]
    assert len(names) == len(set(names)), "repository names must be unique"
    known = set(names)
    for repository in repositories:
        assert COMMIT.fullmatch(repository["commit"]), repository["name"]

    set_ids: list[str] = []
    for compatibility_set in record["compatibility_sets"]:
        set_ids.append(compatibility_set["id"])
        unknown = set(compatibility_set["repository_refs"]) - known
        assert not unknown, (
            f"{compatibility_set['id']}: unknown repository refs {unknown}"
        )
        assert compatibility_set["rollback"], compatibility_set["id"]
        statuses = {
            validation["status"] for validation in compatibility_set["validations"]
        }
        assert statuses <= {"passed", "failed", "not_run", "blocked"}
    assert len(set_ids) == len(set(set_ids)), "compatibility set ids must be unique"

    sequences = [item["sequence"] for item in record["publication_order"]]
    assert sequences == list(range(1, len(sequences) + 1))
    for item in record["publication_order"]:
        assert item["status"] in {"passed", "pending", "blocked"}
        unknown = set(item["repository_refs"]) - known
        assert not unknown, f"publication step {item['sequence']}: {unknown}"

    if record["status"] in {"candidate", "released"}:
        unresolved = {
            validation["id"]
            for compatibility_set in record["compatibility_sets"]
            for validation in compatibility_set["validations"]
            if validation["status"] != "passed"
        }
        assert not unresolved, f"unresolved release validation: {unresolved}"

    print(
        f"validated release record {record['record_id']} with "
        f"{len(repositories)} repositories and {len(set_ids)} compatibility sets"
    )


if __name__ == "__main__":
    main()
