# Workspace Snapshot — 2026-08-17

This is a read-only intake snapshot. Remote HEAD values were queried with
`git ls-remote`; no existing repository was fetched, pulled, reset, or cleaned.

## GitHub Identity and Access

- SSH authentication succeeds as `Tkhkrnx` (profile name: Pharos Peng).
- At capture time the contributor login and Git author identity were not yet
  confirmed. Later on 2026-08-17, the user confirmed `Tkhkrnx` / Pharos Peng;
  the documentation repository was then configured with that local identity.
- The `gh` CLI and `GITHUB_TOKEN`/`GH_TOKEN` environment variables are absent.
- Therefore authenticated issue/PR search, private repository discovery,
  notification intake, and complete review-request collection are not yet
  available.

## Local Repositories

`Local = remote` only compares the checked-out commit with the remote's current
default-branch HEAD. It does not imply that the repository has no other remote
branches or pending work.

| Repository | Branch | Local HEAD | Remote HEAD | Dirty paths | State |
|---|---|---|---|---:|---|
| `EvoScientist` | `main` | `b98fc430fb40` | `2faebc8083a3` | 0 | stale checkout |
| `ascend-runtime-manager` | `main` | `2a113e514fb4` | `27c0b994720f` | 0 | stale checkout |
| `claude-code-hust` | `main` | `817d723771db` | `817d723771db` | 0 | current |
| `fcs-domestic-chip-llm-recsys` | `main` | `74ea8cbe0002` | `8c588133c429` | 0 | stale checkout |
| `triton-ascend-hust` | `main` | `0e1c7ed1aa5f` | `816cd9a7737b` | 0 | stale checkout |
| `vllm-ascend-hust` | `main` | `03a12f9bddd9` | `5328a24b1627` | 7 | stale and dirty; preserve |
| `vllm-ascend-quant-hust` | `main` | `80bc5130427a` | `80bc5130427a` | 0 | current |
| `vllm-hust` | `main` | `6a71cd4bcf2d` | `83ecd99f5ef2` | 2 | stale and dirty; preserve |
| `vllm-hust-benchmark` | `main` | `52182b41b3f8` | `eecf8f8a3314` | 0 | stale checkout |
| `vllm-hust-dev-hub` | `main` | `34c7d25595b3` | `dbf1c5a7458d` | 0 | stale checkout |
| `vllm-hust-docs` | contribution workflow branch | `5f7bbf6091e7` | `5f7bbf6091e7` | workflow files | isolated setup work |
| `vllm-hust-org-profile` | `main` | `2d42cf575a8f` | `69076699b75f` | 0 | stale checkout |
| `vllm-hust-perf-analyzer` | `main` | `1931cc7a4711` | `7488536b73d2` | 0 | stale checkout |
| `vllm-hust-website` | `main` | `2a25315cde6b` | `bb6c67eac980` | 0 | stale checkout |
| `vllm-hust-workstation` | `main` | `e770812cc31f` | `bcb6f47ba136` | 0 | stale checkout |

## Protected Existing Changes

### `vllm-hust`

- modified: `vllm/v1/worker/gpu_worker.py` (six added lines)
- untracked backup: `vllm/v1/worker/gpu_worker.py.pre-npu-allocator-guard`

### `vllm-ascend-hust`

- six modified source files under device, layernorm, rotary embedding, and Qwen
  patch paths (20 insertions and 26 deletions in total)
- untracked backup: `vllm_ascend/patch/worker/patch_qwen3vl.py.bak_qbi_20260725`

The snapshot deliberately does not infer ownership or intent from these diffs.
Do not delete, stash, commit, rebase, or include them in new work without user
direction.

## Safe Start Procedure for the Next Task

1. Use the confirmed `Tkhkrnx` / Pharos Peng identity.
2. Read the live issue/review queue with authenticated access.
3. Select the owning repository and fetch only that repository.
4. Create a clean branch/worktree from the current remote default branch.
5. Record the task issue, hypothesis, baseline, and acceptance criteria before
   implementation.
6. Leave the two protected dirty working trees untouched.
