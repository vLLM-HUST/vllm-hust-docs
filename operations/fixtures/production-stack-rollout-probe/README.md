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

The newer files in this directory extend the historical Helm fixture:

- `Dockerfile.operator-arm64` carries the exact upstream Go controller binary
  in `scratch` for the isolated arm64 test;
- `vllmrouter-e2e.yaml` exercises official CR reconciliation;
- `mock_backend.py`, `Dockerfile.mock-backend`, and `mock-backend.yaml` provide
  a deterministic OpenAI-compatible external endpoint;
- `router-hpa-deployment.yaml`, `router-hpa.yaml`, and `router-load.yaml`
  exercise real Metrics API scaling without claiming model inference; and
- `operator-hpa-conflict.yaml` is a negative-only two-writer ownership test.

The extended run passes controller business reconciliation, Router-to-external
backend traffic, and a real CPU-driven 1-to-3 scaling decision. It does not
claim real model inference. The HPA is intentionally attached to a separately
owned Router Deployment: the negative fixture proves the current controller
will fight an HPA that also writes its owned Deployment's replica count.
