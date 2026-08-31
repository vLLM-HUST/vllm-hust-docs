# Production Stack rollout probe

This fixture validates Helm and Kubernetes lifecycle behavior without loading a
model or requesting an accelerator. It is test-only evidence, not a production
Router image and not a serving-data-path benchmark.

`values-v1.yaml` deploys one Router pod tagged `v1`; `values-v2.yaml` deploys
two pods tagged `v2`. The OCI fixture ignores the chart's Router arguments and
serves `/health` on port 8000 so Kubernetes startup, readiness, and liveness
probes are deterministic.

`values-controller-hpa.yaml` additionally enables the LoRA controller
Deployment and the Router CPU HorizontalPodAutoscaler. The probe image exposes
the controller's `/healthz` and `/readyz` endpoints on port 8081 and runs as
UID/GID 65532 so the chart's non-root security context remains effective.

An external test operator performs the lifecycle. Extension Manager must only
render and check evidence; it must never execute these commands itself.

Expected sequence:

1. Build and load the fixture as tags `v1` and `v2` into an isolated cluster.
2. Install the official Production Stack chart with `values-v1.yaml` and wait
   for a `1/1` rollout.
3. Upgrade with `values-v2.yaml` and wait for `2/2`.
4. Roll back to revision 1 and verify tag `v1` with `1/1` available.
5. Attempt an upgrade with an absent image and
   `--rollback-on-failure`; require a non-zero upgrade result and recovery to
   tag `v1` with `1/1` available.
6. Uninstall and require all release-labelled resources to be absent.
7. Delete the isolated cluster, test image tags, and staging directory.

Passing this fixture does not satisfy the remaining controller/autoscaler
business-logic or Router-to-model traffic gates. Without a metrics server, HPA
object/controller reconciliation can be checked, but an actual CPU-driven scale
decision cannot be claimed.
