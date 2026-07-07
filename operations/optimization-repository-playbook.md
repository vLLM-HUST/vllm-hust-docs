# Optimization Repository Playbook

This document describes a reusable workflow for research optimization
repositories that depend on external runtime stacks, hardware-specific
launchers, and paper-facing experiments. It is intentionally project-neutral:
replace placeholder names such as `<optimization-repo>`, `<runtime-repo>`,
`<device-id>`, and `<project-feature>` with the names used by a specific
project.

## Goals

An optimization repository should be self-contained enough that another
teammate can reproduce code, experiments, figures, and paper claims from:

1. the parent optimization repository;
2. its pinned submodules;
3. documented secrets or local environment variables;
4. recorded hardware/runtime provenance.

The repository should not depend on untracked sibling checkouts, personal shell
state, long-lived services, or undocumented containers.

## Repository Roles

Use the parent repository as the source of truth for:

- optimization code and policies;
- experiment scripts and result aggregation;
- figure and paper-generation code;
- submodule pointers;
- reproducibility documentation.

Use submodules for external code that must be patched, pinned, or used as a
runtime carrier:

- serving engines;
- accelerator plugins;
- runtime managers;
- container/dev-hub launchers;
- compiler or kernel stacks;
- reference implementations used for comparison or design context.

Do not use symlinks for runtime dependencies. A submodule must be an
independent checkout owned by the parent repository:

```bash
test ! -L third_party/<dependency>
cat third_party/<dependency>/.git
git -C third_party/<dependency> rev-parse --git-dir
```

The `.git` file should point into the parent repository's
`.git/modules/third_party/<dependency>` directory.

## Branch Policy

Use project-specific feature branches in every patched dependency. Do not patch
`main` directly inside a submodule.

Recommended branch pattern:

```text
feature/<project-or-optimization-name>-<purpose>
```

Examples of purposes:

- `runtime-integration`
- `managed-launch`
- `prefix-admission`
- `graph-compat`
- `kernel-pin`

Keep feature branches narrow. If a branch carries unrelated upstream changes,
rebase it onto the current upstream `main` so the branch contains only the
project-specific delta:

```bash
git -C third_party/<dependency> fetch origin main
git -C third_party/<dependency> checkout feature/<project-feature>
git -C third_party/<dependency> rebase origin/main
git -C third_party/<dependency> rev-list --left-right --count origin/main...HEAD
```

The ideal result is `0 N`, where `N` is the number of project-specific commits.
If `N` is large, confirm that every commit belongs to the project before
pushing.

When rebasing a shared feature branch, use:

```bash
git -C third_party/<dependency> push --force-with-lease origin feature/<project-feature>
```

Do not use plain `--force`.

## When To Open Pull Requests

Do not open upstream PRs just because a submodule branch exists.

Open a PR only when the change is useful to the upstream project now, independent
of whether the optimization paper or prototype is complete. Good PR candidates:

- a concrete bug fix with a clear failing path;
- a generic launch or runtime safety improvement;
- a compatibility fix that benefits multiple users;
- documentation for a reusable workflow;
- test coverage for upstream behavior.

Keep project-specific experimental hooks pinned in submodule feature branches
until the optimization design and evidence are stable. These branches can later
be split into upstreamable pieces.

Before opening a PR:

```bash
git -C third_party/<dependency> diff --stat origin/main..HEAD
git -C third_party/<dependency> log --oneline origin/main..HEAD
```

If the diff includes unrelated files or historical branch drift, rebase or
split the branch first.

## Submodule Update Workflow

When a dependency needs a change:

1. Enter the submodule.
2. Check out the project feature branch.
3. Make and test the change inside the submodule.
4. Commit and push the submodule branch.
5. Return to the parent repository.
6. Stage only the submodule pointer and any parent scripts/docs that depend on
   it.
7. Commit and push the parent repository.

Template:

```bash
git -C third_party/<dependency> checkout feature/<project-feature>
# edit and test
git -C third_party/<dependency> add <files>
git -C third_party/<dependency> commit -m "<short dependency change>"
git -C third_party/<dependency> push origin feature/<project-feature>

git add third_party/<dependency> <parent-files>
git commit -m "<short parent pointer/update change>"
git push origin <parent-branch>
```

Never make the parent repository depend on `/home/<user>/<dependency>` or any
other external checkout. If a useful change exists outside the submodule, port
it manually into the submodule branch.

## Graduating Optimization Results

When an optimization project becomes mature enough to merge back into long-term
runtime repositories, do not copy the whole parent repository into a runtime
stack. Treat the parent optimization repository as the reproducibility and
evidence layer, then graduate only the maintainable runtime pieces into their
proper homes.

Use this three-layer model:

1. The parent optimization repository keeps the full research record:
   experiment scripts, paper figures, result aggregation, run manifests,
   workload definitions, and submodule pointers.
2. Submodule feature branches carry runtime changes while the design is still
   evolving.
3. Long-term repositories such as `vllm-hust`, `vllm-ascend-hust`,
   `triton-ascend-hust`, `dev-hub`, or benchmark repositories receive small,
   reviewable, tested slices after the ownership boundary is clear.

Classify every change before moving it:

- generic bug fixes belong in the upstream project or in the corresponding
  long-term vLLM-HUST runtime repository;
- generic performance improvements should move with a benchmark, a compatibility
  story, and usually a guarded/default-off integration path first;
- project-specific mechanisms should remain on the optimization feature branch
  until the design and evidence are stable;
- experimental hooks should stay in the optimization repository or submodule
  feature branch unless they have a clear production interface;
- experiment harnesses, workload generation, aggregation, and paper-reproduction
  code usually remain in the parent repository, benchmark repository, or
  `dev-hub`, not in the serving engine.

For code that was first written directly in the parent optimization repository,
decide ownership before moving it:

- serving-engine scheduling, cache, request lifecycle, or policy logic belongs
  in `vllm-hust`;
- Ascend backend behavior belongs in `vllm-ascend-hust`;
- compiler, kernel, or Triton runtime behavior belongs in `triton-ascend-hust`;
- launch orchestration and managed experiment entry points belong in `dev-hub`
  or the parent repository;
- paper reproduction, ablations, and result processing stay in the optimization
  parent repository.

Prefer a library-first migration. Add a small internal module or extension point
in the target repository, move the reusable logic there, then update the parent
optimization repository to call that implementation through its submodule
pointer. Avoid one large "optimization merge" PR.

Split graduation into reviewable pull requests such as:

- base interfaces and metadata;
- tracing or instrumentation needed to validate behavior;
- runtime policy implementation behind a flag;
- cache or lifecycle integration;
- benchmark workloads and regression tests;
- default-off integration;
- default-on enablement only after evidence supports it.

After graduation, the parent repository should still reproduce the paper or
optimization result, but its submodule pointers should reference the integrated
branches, merged commits, or released versions instead of carrying duplicate
logic.

## Runtime And Container Rules

Runtime launch scripts must resolve all dependency paths from the parent
repository and its submodules. They should reject external checkouts and
symlinks before starting expensive jobs.

Recommended checks in launch scripts:

- required submodule path exists;
- path is not a symlink;
- real path is under the parent repository's `third_party/`;
- `git rev-parse --show-toplevel` equals the submodule path;
- `git rev-parse --git-dir` points inside parent `.git/modules`;
- container path matches the actual bind mount;
- required device ID matches the user-specified reservation;
- forbidden fallback modes are not enabled.

Secrets should be provided by environment variables or untracked `.env` files.
Never commit API keys, tokens, bearer headers, or private credentials. Logs
should redact secrets before writing command lines.

Container and runtime storage should be configured through documented paths, not
whatever default happens to exist on a machine. If a machine requires storage
under a specific data partition, document the policy in the parent repository
and make launch scripts verify it.

## Experiment Evidence Labels

Every result used in a paper, report, or figure should carry an evidence label.
Use these labels consistently:

- `real-online`: the repository launches or controls the measured serving path;
- `existing-server-probe`: the client probes a server not launched by this
  repository;
- `replay`: recorded or synthetic traces are replayed through a model;
- `simulation/model`: a cost model or analytical model produces the result;
- `projected-profile`: a measured component delta is projected onto a larger
  path;
- `derived-artifact`: CSV, table, figure, or PDF regenerated from existing
  inputs.

Do not describe replay, simulation, projected profiles, or derived artifacts as
measured serving speedups.

## Real Experiment Checklist

Before starting a real hardware experiment:

- confirm the requested device is free;
- confirm the model path exists;
- confirm ports are free;
- confirm old services will not be reused accidentally;
- confirm required submodules are initialized and on expected branches;
- confirm graph/eager/custom-kernel settings match the claim;
- confirm output directories are new or intentionally overwritten;
- record the exact command and environment knobs;
- record parent commit, submodule commits, branches, and dirty status.

If the reserved device becomes occupied, stop. Do not move to another device,
kill unrelated jobs, or downgrade the experiment unless the owner explicitly
changes the constraint.

## Manifest Requirements

Every benchmark output directory should include a manifest such as
`run_metadata.json` or `suite_metadata.json` with:

- evidence label;
- parent repository commit, branch, and dirty status;
- relevant submodule commits, branches, and dirty status;
- hardware device IDs and accelerator type;
- model path and model identity;
- runtime image/container/launcher identity;
- important environment variables, excluding secrets;
- graph/eager/custom-kernel mode;
- workload parameters;
- command entry point;
- timestamp.

Repeated experiments should additionally record:

- repetition count;
- per-repetition result directories;
- aggregation convention;
- center statistic, such as median;
- error convention, such as IQR or confidence interval.

## Result Hygiene

Keep invalid or interrupted runs out of paper claims. If a run starts but does
not produce valid results, mark it explicitly:

```text
BLOCKED.txt
FAILED.txt
```

The note should say why the run is invalid and whether any partial logs are only
debugging evidence.

Do not delete failed evidence silently. Failed graph-mode launches, device
conflicts, import errors, and runtime incompatibilities often explain the next
engineering step.

## Paper And Figure Discipline

Use macros or a small term table for system names and baseline names. This
prevents figures, captions, tables, and prose from drifting.

For claims:

- state what was measured;
- state where it was measured;
- state whether it is real-online, replay, or derived;
- avoid universal speedup language unless the evaluation supports it;
- describe negative or boundary cases directly.

For figures:

- regenerate figures from checked-in data or manifest-backed results;
- use stable colors and labels for the system and baselines;
- show repeated runs with median plus error bars when the measurement is noisy;
- visually inspect the final PDF, not only the source figure files.

## Safe Git Practices

The parent repository may have unrelated dirty files. Stage explicit paths only.

Useful commands:

```bash
git status --short
git diff --stat -- <paths>
git add <explicit-paths>
git diff --cached --stat
git diff --cached --name-status
git commit -m "<message>"
git push origin <branch>
```

For submodules:

```bash
git submodule status --recursive
git -C third_party/<dependency> status --short
git -C third_party/<dependency> branch --show-current
git -C third_party/<dependency> rev-parse HEAD
```

Do not run destructive commands such as `git reset --hard`, `git clean -fd`, or
`git checkout -- .` in a shared or dirty worktree unless the owner explicitly
requests it.

## Handoff Checklist

Before handing work to another teammate:

- parent branch and commit are pushed;
- all changed submodule branches are pushed;
- parent submodule pointers are committed and pushed;
- no dependency path is a symlink;
- feature branches are rebased or intentionally documented as not rebased;
- PRs exist only for upstream-ready fixes;
- invalid experiments are marked as invalid;
- latest valid experiment directories are named in the roadmap or handoff;
- paper claims match the evidence labels;
- commands needed for the next step are documented.

## Minimal Onboarding Command Set

For a fresh checkout:

```bash
git clone <parent-repo-url> <optimization-repo>
cd <optimization-repo>
git submodule update --init
```

Before running experiments:

```bash
git submodule status --recursive
find third_party -maxdepth 2 -type l -print
```

Then follow the project-specific runbook for environment variables, devices,
models, and launch commands.
