# vLLM-HUST Current vs Baseline Perf Roadmap

## Current Status

- Current target: `/home/shuhao/vllm-hust` + `/home/shuhao/vllm-ascend-hust`
- Baseline target: `v0.18.0` source trees under `/tmp/vllm-v0180` + `/tmp/vllm-ascend-v0180`
- Test environment: `vllm-hust-dev` conda env for current, official env for baseline, no `.venv`
- Canonical quick workload: `Qwen2.5-7B-Instruct`, `TP=1`, `load-format dummy`, `input-len=1024`, `output-len=32/256`, `float16`, `enforce-eager`

## Working Conclusion

- For the tested quick dummy latency workload, there is no current evidence that current is slower than baseline.
- Fast rerun result already showed current ahead of baseline on the non-profiled quick compare path.
- Same-spec profiled full run showed current and baseline effectively tied in end-to-end latency, while TraceLoom still showed different idle distribution.
- Therefore the performance conclusion should be stated as: current is not worse than baseline on the tested benchmark slice, but there is still an unresolved structural execution difference.

## Confirmed Findings

1. Rope is not the root cause.
   - Removing rope-local contiguous materialization did not improve end-to-end latency.
   - FIA layout and value-path probes matched between current and baseline on the tested Qwen2 path.

2. Scheduler shape is not the root cause.
   - Current and baseline iteration-detail logs matched on the same card.
   - Disabling `scheduler_reserve_full_isl` did not collapse the TraceLoom tree difference.

3. Runner non-spec `seq_lens` materialization was a real divergence, but not the root cause of the remaining tree gap.
   - Before the fix, current `_prepare_inputs` probe rows had `seq_lens: null` while baseline had concrete values.
   - After the fix in `vllm_ascend/worker/model_runner_v1.py`, current and baseline runner probes matched for the first 16 rows after normalizing request ids.
   - The same-card mini TraceLoom tree still did not converge to baseline afterward.

4. Attention builder source selection is also not sufficient.
   - A follow-up experiment making the builder prefer `seq_lens_cpu` over `_seq_lens_cpu` in non-spec mode did not collapse the late-loop difference.
   - That experiment was reverted.

## Explicit Non-Goals For The Next Round

- Do not reopen rope-local micro-optimizations first.
- Do not spend time on scheduler reserve policy first.
- Do not treat one noisy single-run latency delta as the decision signal.
- Do not widen to unrelated models until the Qwen2.5-7B dummy eager slice is explained.

## Next Roadmap

### Phase 1: Lock the decision criterion

1. Keep using the same-card NPU2 quick workload as the primary discriminator.
2. Treat TraceLoom loop-tree convergence plus repeated latency stability as the acceptance signal.
3. Record every new experiment against the same three comparison points:
   - old current
   - current with runner fix
   - baseline official v0.18.0

### Phase 2: Probe the next direct control surface

1. Instrument later attention metadata consumers rather than upstream schedulers or rope.
2. Focus on the path that still produces current-only late loops `N046 x28`, `N059 x28`, `N072 x28`, `N085 x8` versus baseline `N044 x6 -> N048 x28` and `N061 x23`.
3. Prioritize these surfaces:
   - `vllm_ascend/attention/attention_v1.py`
   - `vllm_ascend/attention/mla_v1.py`
   - `split_decodes_and_prefills` and related metadata splitting decisions
   - any kernel-selection or metadata-shaping branch that changes late decode grouping

### Phase 3: Run one-hop falsifiable experiments

1. Add runtime probes around attention builder outputs for late decode iterations.
2. Compare current vs baseline for:
   - `num_decodes`
   - `num_prefills`
   - `num_decode_tokens`
   - `num_prefill_tokens`
   - final per-iteration `seq_lens` and `query_lens`
   - any branch selecting chunked vs decode metadata forms
3. If a concrete mismatch appears, patch only that local decision point and rerun the same NPU2 mini profile.

### Phase 4: Revalidate beyond the mini profile

1. If the tree converges on the mini workload, rerun the larger quick compare benchmark.
2. Repeat at least one non-profiled latency comparison to check that the change helps user-visible latency rather than only changing TraceLoom structure.
3. Only after that consider expanding to a more realistic dataset or serving workload.

## Practical Success Criteria

- Current remains no worse than baseline on the quick benchmark.
- Current TraceLoom tree no longer shows the extra late-loop split pattern.
- The explanation is local, falsifiable, and merge-safe.

## Latest Artifact Set

- Runner probe alignment:
  - `/home/shuhao/vllm-hust-perf-analyzer/out/current-runner-probe.jsonl`
  - `/home/shuhao/vllm-hust-perf-analyzer/out/official-runner-probe.jsonl`
- Same-card mini profiles:
  - `/home/shuhao/vllm-hust-perf-analyzer/out/current-npu2-mini-analysis/summary.md`
  - `/home/shuhao/vllm-hust-perf-analyzer/out/current-npu2-mini-patched-analysis/summary.md`
  - `/home/shuhao/vllm-hust-perf-analyzer/out/official-npu2-mini-analysis/summary.md`
