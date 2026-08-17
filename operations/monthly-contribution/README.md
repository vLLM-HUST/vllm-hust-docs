# Monthly Contribution and Evidence Workflow

This directory turns monthly engineering work into a truthful, auditable record
for weekly reporting and self-review. It complements the optimization evidence
rules in [Optimization Repository Playbook](../optimization-repository-playbook.md).

## Objective

Prioritize substantive inference-engine performance work while keeping all
other contribution categories healthy. The score targets below are internal
operating targets, not official grading thresholds; the supplied form only
states each category's maximum score.

| Category | Max | Internal evidence target |
|---|---:|---|
| Performance improvement | 7 | At least one end-to-end, repeated, correctness-checked improvement, ideally with a second independent optimization or regression guard |
| Code development | 4 | Several merged, tested, coherent code changes whose necessity and ownership are clear |
| Teamwork | 3 | Visible co-design, debugging, handoff, or unblock work with links and outcomes |
| Documentation | 2 | Reproducible technical documentation such as an RFC, runbook, benchmark method, or user guide |
| Code review | 1 | Substantive reviews on multiple PRs, including validation performed and resolution of blocking findings |
| Issue closure | 0.5 | At least one issue taken from reproducible problem to verified closure |
| General/operational work | 2 | CI, release, benchmark publication, meeting, triage, or project-maintenance outcomes with durable artifacts |

Counts alone are not evidence of impact. A large change should remain one PR if
that is the clearest review unit; independent outcomes should be separate PRs.

## Evidence Ledger

Create one row as soon as an activity produces a stable URL. Do not wait until
month end.

| Date | Category | Repository | Artifact | Outcome | Validation | Status |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | performance/code/etc. | `vLLM-HUST/repo` | issue/PR/commit/review/report URL | one verifiable sentence | tests or benchmark URL | planned/open/merged/closed |

An artifact may support more than one category only when the note explains the
distinct evidence. For example, an optimization PR can support performance for
its measured delta and code development for its tested implementation. Do not
duplicate the same sentence across categories.

## Weekly Loop

1. **Triage:** review direct mentions, requested reviews, assigned issues,
   authored PRs, CI failures, and stale handoffs.
2. **Select:** choose one explicit task. If none is assigned, choose one
   falsifiable performance hypothesis with a baseline workload.
3. **Implement:** use a dedicated branch/worktree, atomic commits, tests, and a
   coherent PR.
4. **Measure:** retain exact revisions, environment, raw data, repetitions,
   summary statistics, and correctness results.
5. **Collaborate:** review PMC requests early and follow comments through to a
   recorded outcome.
6. **Report:** update the weekly report and monthly ledger with stable links.

## Performance Claim Gate

A result is ready for self-review only if another contributor can answer all of
these from the linked artifacts:

- What baseline and candidate commits were compared?
- What hardware, software stack, model, workload, and serving flags were used?
- How many warmups and measured repetitions were run?
- What were the absolute baseline and candidate values?
- What was the delta, variance, and any trade-off in TTFT, ITL, throughput,
  latency, memory, or correctness?
- Is the result end-to-end measured, replayed, simulated, projected, or derived?
- Which tests or output comparisons protect correctness?
- Where are the raw artifacts or checksums?

Neutral and negative experiments should still be recorded because they narrow
the search space, but they must not be presented as performance wins.

## Files

- [August 2026 plan](2026-08-plan.md)
- [August GitHub intake snapshot](2026-08-github-snapshot.md)
- [Workspace intake snapshot](workspace-snapshot-2026-08-17.md)
- [Weekly report template](templates/weekly-report.md)
- [Monthly self-review template](templates/monthly-self-review.md)

The contribution collector in `scripts/collect_monthly_contributions.py`
creates a link-oriented GitHub snapshot. It does not score or infer impact.

```bash
export GITHUB_LOGIN='<confirmed-login>'
export GITHUB_TOKEN='<fine-grained-token-with-required-read-access>'
python scripts/collect_monthly_contributions.py \
  --since 2026-08-01 --until 2026-08-31 \
  --output operations/monthly-contribution/2026-08-github-snapshot.md
```

Keep tokens in environment variables. Never place them in reports, shell
history committed to Git, or command output.
