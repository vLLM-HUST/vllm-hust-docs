#!/usr/bin/env python3
"""Collect a link-oriented GitHub contribution snapshot for self-review.

The collector intentionally does not assign scores or infer engineering impact.
It gathers candidate evidence that must still be checked against benchmark,
test, discussion, and review artifacts by a human.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"


class GitHubError(RuntimeError):
    """A GitHub API request failed without exposing credentials."""


@dataclass(frozen=True)
class SearchSpec:
    key: str
    title: str
    query: str
    note: str = ""


class GitHubClient:
    def __init__(self, token: str | None) -> None:
        self._token = token

    def get(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        url = f"{API_ROOT}{path}?{urlencode(params)}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "vllm-hust-monthly-evidence-collector",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            try:
                body = json.load(error)
                message = body.get("message", str(error))
            except (json.JSONDecodeError, AttributeError):
                message = str(error)
            hint = ""
            if error.code in {401, 403}:
                hint = (
                    " Set GITHUB_TOKEN (or GH_TOKEN) to a fine-grained token "
                    "with read access to the required organization metadata."
                )
            raise GitHubError(f"GitHub API returned {error.code}: {message}.{hint}") from error
        except URLError as error:
            raise GitHubError(f"GitHub API connection failed: {error.reason}") from error

    def search(self, path: str, query: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        while page <= 10:
            payload = self.get(
                path,
                {"q": query, "per_page": 100, "page": page, "sort": "updated"},
            )
            batch = payload.get("items", [])
            if not isinstance(batch, list):
                raise GitHubError("GitHub search response did not contain an item list")
            items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org", default="vLLM-HUST", help="GitHub organization")
    parser.add_argument(
        "--user",
        default=os.environ.get("GITHUB_LOGIN"),
        help="GitHub login (or set GITHUB_LOGIN)",
    )
    parser.add_argument("--since", required=True, help="inclusive start date, YYYY-MM-DD")
    parser.add_argument("--until", required=True, help="inclusive end date, YYYY-MM-DD")
    parser.add_argument("--output", type=Path, help="Markdown output; stdout if omitted")
    parser.add_argument("--json-output", type=Path, help="optional raw normalized JSON")
    parser.add_argument(
        "--no-commits",
        action="store_true",
        help="skip commit search when PR evidence is sufficient",
    )
    return parser.parse_args()


def validate_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise SystemExit(f"invalid date {value!r}; expected YYYY-MM-DD") from error


def deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    for item in items:
        url = item.get("html_url")
        if isinstance(url, str):
            by_url[url] = item
    return sorted(
        by_url.values(),
        key=lambda item: item.get("updated_at") or item.get("commit", {}).get("author", {}).get("date", ""),
        reverse=True,
    )


def normalize_issue(item: dict[str, Any]) -> dict[str, Any]:
    repository_url = item.get("repository_url", "")
    repo = repository_url.rsplit("/", 1)[-1] if repository_url else "unknown"
    return {
        "repository": repo,
        "number": item.get("number"),
        "title": item.get("title", ""),
        "url": item.get("html_url", ""),
        "state": item.get("state", ""),
        "created_at": item.get("created_at", ""),
        "updated_at": item.get("updated_at", ""),
        "closed_at": item.get("closed_at", ""),
        "draft": item.get("draft", False),
    }


def normalize_commit(item: dict[str, Any]) -> dict[str, Any]:
    repository = item.get("repository", {}).get("name", "unknown")
    commit = item.get("commit", {})
    message = commit.get("message", "").splitlines()[0]
    author = commit.get("author", {})
    return {
        "repository": repository,
        "sha": item.get("sha", ""),
        "title": message,
        "url": item.get("html_url", ""),
        "date": author.get("date", ""),
    }


def markdown_escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def item_link(item: dict[str, Any]) -> str:
    title = markdown_escape(item.get("title", "untitled"))
    url = item.get("url", "")
    return f"[{title}]({url})" if url else title


def render_markdown(
    org: str,
    user: str,
    since: str,
    until: str,
    sections: list[tuple[SearchSpec, list[dict[str, Any]]]],
) -> str:
    lines = [
        f"# GitHub Contribution Snapshot — {since} to {until}",
        "",
        f"> Organization: `{org}`  ",
        f"> Contributor: `{user}`  ",
        "> Generated evidence candidates; verify impact and event dates before self-review.",
        "",
        "This snapshot is an intake aid, not a score. Search results can include an",
        "artifact because it was updated during the interval even when the underlying",
        "review or mention occurred earlier.",
        "",
    ]

    for spec, items in sections:
        lines.extend([f"## {spec.title} ({len(items)})", ""])
        if spec.note:
            lines.extend([spec.note, ""])
        if not items:
            lines.extend(["_No matching public/accessible artifacts found._", ""])
            continue

        lines.extend(["| Repository | Artifact | State/date |", "|---|---|---|"])
        for item in items:
            state_or_date = item.get("state") or item.get("date") or item.get("updated_at")
            lines.append(
                "| {repo} | {artifact} | {state} |".format(
                    repo=markdown_escape(item.get("repository")),
                    artifact=item_link(item),
                    state=markdown_escape(state_or_date),
                )
            )
        lines.append("")

    lines.extend(
        [
            "## Manual Evidence Still Required",
            "",
            "- review comment URLs and what was validated or changed;",
            "- CI/test links and merge/adoption state;",
            "- performance baseline, absolute values, variance, and raw artifacts;",
            "- co-debugging, handoff, meeting, and operational outcomes;",
            "- confirmation that each event occurred inside the reporting interval.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if not args.user:
        raise SystemExit("--user or GITHUB_LOGIN is required")
    since = validate_date(args.since)
    until = validate_date(args.until)
    if since > until:
        raise SystemExit("--since must be on or before --until")

    period = f"{since}..{until}"
    prefix = f"org:{args.org}"
    specs = [
        SearchSpec(
            "authored_prs",
            "Authored PRs created or merged in period",
            "",
            "Created and merged searches are combined and deduplicated.",
        ),
        SearchSpec(
            "reviewed_prs",
            "PRs reviewed by contributor and updated in period",
            f"{prefix} is:pr reviewed-by:{args.user} updated:{period}",
            "Confirm the actual review submission date and link the review comment.",
        ),
        SearchSpec(
            "pending_reviews",
            "Open review requests",
            f"{prefix} is:pr is:open review-requested:{args.user}",
        ),
        SearchSpec(
            "authored_issues",
            "Issues authored in period",
            f"{prefix} is:issue author:{args.user} created:{period}",
        ),
        SearchSpec(
            "involved_closed_issues",
            "Closed issues involving contributor",
            f"{prefix} is:issue involves:{args.user} closed:{period}",
            "Involvement does not prove that the contributor closed the issue.",
        ),
        SearchSpec(
            "mentions",
            "Direct mentions on artifacts updated in period",
            f"{prefix} mentions:{args.user} updated:{period}",
            "Confirm the mention timestamp and whether a response is still needed.",
        ),
    ]

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    client = GitHubClient(token)
    normalized: dict[str, list[dict[str, Any]]] = {}
    try:
        authored = client.search(
            "/search/issues",
            f"{prefix} is:pr author:{args.user} created:{period}",
        )
        authored.extend(
            client.search(
                "/search/issues",
                f"{prefix} is:pr author:{args.user} merged:{period}",
            )
        )
        normalized["authored_prs"] = [normalize_issue(item) for item in deduplicate(authored)]

        for spec in specs[1:]:
            results = client.search("/search/issues", spec.query)
            normalized[spec.key] = [normalize_issue(item) for item in deduplicate(results)]

        if not args.no_commits:
            commit_spec = SearchSpec(
                "commits",
                "Commits authored in period",
                f"{prefix} author:{args.user} author-date:{period}",
                "Prefer PR-level evidence when commits are part of a pull request.",
            )
            specs.append(commit_spec)
            commits = client.search("/search/commits", commit_spec.query)
            normalized[commit_spec.key] = [normalize_commit(item) for item in deduplicate(commits)]
    except GitHubError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    sections = [(spec, normalized.get(spec.key, [])) for spec in specs]
    markdown = render_markdown(args.org, args.user, since, until, sections)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "organization": args.org,
            "user": args.user,
            "since": since,
            "until": until,
            "sections": normalized,
        }
        args.json_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
