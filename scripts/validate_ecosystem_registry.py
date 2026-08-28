#!/usr/bin/env python3
"""Validate invariants that are not delegated to a JSON Schema runtime."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "ecosystem-components.json"
PORTFOLIO = ROOT / "registry" / "repository-portfolio.json"

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

    portfolio = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
    assert portfolio["schema_version"] == "1.0"
    assert portfolio["canonical_owner"] == "vLLM-HUST/vllm-hust-docs"

    repositories = portfolio["repositories"]
    names = [repository["name"] for repository in repositories]
    urls = [repository["url"] for repository in repositories]
    assert len(names) == len(set(names)), "repository names must be unique"
    assert len(urls) == len(set(urls)), "repository URLs must be unique"

    component_ids = set(ids)
    portfolio_component_ids: set[str] = set()
    for repository in repositories:
        unknown = set(repository["component_ids"]) - component_ids
        assert not unknown, f"{repository['name']}: unknown component ids {unknown}"
        portfolio_component_ids.update(repository["component_ids"])
        if repository["lifecycle"] == "archived":
            assert repository["relation_to_runtime"] == "historical_only"

    organization_components = {
        component["id"]
        for component in components
        if component["canonical_repository"]
        and component["canonical_repository"].startswith(
            "https://github.com/vLLM-HUST/"
        )
    }
    missing_components = organization_components - portfolio_component_ids
    assert not missing_components, (
        "organization-owned components missing from repository portfolio: "
        f"{missing_components}"
    )

    print(
        f"validated {len(components)} ecosystem components and "
        f"{len(repositories)} organization repositories"
    )


if __name__ == "__main__":
    main()
