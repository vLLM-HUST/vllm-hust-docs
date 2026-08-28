#!/usr/bin/env python3
"""Validate invariants that are not delegated to a JSON Schema runtime."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "ecosystem-components.json"

REQUIRED_FIELDS = {
    "id",
    "name",
    "artifact_type",
    "system_role",
    "integration_contracts",
    "execution_planes",
    "deployment_topology",
    "delivery_model",
    "ownership",
    "maturity",
    "canonical_repository",
    "summary_en",
    "summary_zh",
    "evidence_level",
}


def main() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["canonical_owner"] == "vLLM-HUST/vllm-hust-docs"

    components = payload["components"]
    ids = [component["id"] for component in components]
    assert len(ids) == len(set(ids)), "component ids must be unique"

    for component in components:
        missing = REQUIRED_FIELDS - component.keys()
        assert not missing, f"{component.get('id', '<unknown>')}: missing {missing}"
        assert component["execution_planes"], f"{component['id']}: no execution plane"
        assert len(component["execution_planes"]) == len(
            set(component["execution_planes"])
        )
        assert len(component["integration_contracts"]) == len(
            set(component["integration_contracts"])
        )

    print(f"validated {len(components)} ecosystem components")


if __name__ == "__main__":
    main()
