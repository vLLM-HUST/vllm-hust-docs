# Public OpenAI-Compatible API Exposure for vllm-hust

This guide records the operational path used to expose a vllm-hust backend on a public OpenAI-compatible endpoint while keeping workstation integration healthy.

## Scope

- Backend runtime: vllm-hust on the A100 host
- Workstation UI: vllm-hust-workstation
- Public endpoints:
  - `https://api.sage.org.ai/v1`
  - `https://ws.sage.org.ai/`
- Public ingress: Cloudflare Tunnel

## Target Outcome

- The backend is reachable through an OpenAI-compatible public base URL.
- Unauthenticated access to `/v1/*` is rejected.
- Workstation continues to detect the upstream engine as online.
- Health checks continue to work after authentication is enabled.

## Local and Public Endpoints

Typical deployment layout:

- Local backend: `http://127.0.0.1:8080/v1/models`
- Local workstation: `http://127.0.0.1:3001/api/models`
- Public backend: `https://api.sage.org.ai/v1/models`
- Public workstation: `https://ws.sage.org.ai/api/models`

## Authentication Model

vLLM protects the OpenAI-compatible `/v1/*` routes with `VLLM_API_KEY`.

Workstation keeps its own source of truth in `.env` through `VLLM_HUST_API_KEY`, then forwards the same bearer token when it talks to the backend.

Important limitation:

- `VLLM_API_KEY` protects `/v1/*` only.
- Non-`/v1` routes still need Cloudflare-side filtering and rate limiting.

## Required Runtime Wiring

### 1. Set the shared API key in workstation `.env`

Set a real secret instead of `not-required`:

```dotenv
VLLM_HUST_API_KEY=sk-REPLACE-WITH-A-REAL-SECRET
```

Do not commit real production secrets into shared documentation or public repositories.

### 2. Propagate the key into backend runtime

`vllm-hust-workstation/scripts/run_backend_systemd.sh` should map the workstation-side key into backend runtime as `VLLM_API_KEY`.

Effective rule:

- use `WORKSTATION_VLLM_API_KEY` if set
- otherwise use `VLLM_HUST_API_KEY`
- if the value is empty or `not-required`, do not export `VLLM_API_KEY`

This keeps workstation and backend aligned without duplicating configuration sources.

### 3. Make health checks authentication-aware

`vllm-hust-workstation/scripts/manage_public_stack.sh` must load `.env` and add:

```bash
Authorization: Bearer ${VLLM_HUST_API_KEY}
```

for backend `/v1/models` probes.

Without this, the stack status command will report false negatives after auth is enabled.

## Deployment Procedure

### Backend

1. Update `VLLM_HUST_API_KEY` in `.env`.
2. Restart the backend service so `VLLM_API_KEY` is exported into the actual vllm-hust process.
3. Verify:

```bash
curl -sS http://127.0.0.1:8080/v1/models
curl -sS http://127.0.0.1:8080/v1/models \
  -H 'Authorization: Bearer sk-REPLACE-WITH-A-REAL-SECRET'
```

Expected behavior:

- unauthenticated request returns `401 Unauthorized`
- authenticated request returns model metadata

### Workstation

If `VLLM_HUST_API_KEY` changes, a restart alone is not enough.

Reason:

- workstation runtime configuration is embedded into the built Next.js standalone output
- stale deployed runtime can keep using `not-required` even when source `.env` is already updated

Required action:

```bash
cd /home/shuhao/vllm-hust-workstation
./scripts/deploy_workstation.sh ci-deploy
```

After redeploy, verify:

```bash
curl -sS http://127.0.0.1:3001/api/models
curl -sS https://ws.sage.org.ai/api/models
```

Expected fields:

- `"upstreamAvailable": true`
- `"engineReady": true`

## Cloudflare Checklist

Cloudflare Tunnel should publish at least two hostnames:

- `api.sage.org.ai` -> backend service
- `ws.sage.org.ai` -> workstation service

Recommended Cloudflare actions:

1. Confirm the tunnel public hostname for `api.sage.org.ai` points to the backend origin.
2. Add WAF rules to block or challenge non-`/v1` paths on `api.sage.org.ai`.
3. Add rate limiting for `POST /v1/chat/completions` and `POST /v1/completions`.
4. Keep browser-style Cloudflare Access off this endpoint if standard OpenAI SDK compatibility is required.
5. Preserve TLS termination and origin connectivity settings already used by the workstation hostname unless backend-specific constraints require a split policy.

## Validation Commands

### Public model list

```bash
curl -sS https://api.sage.org.ai/v1/models \
  -H 'Authorization: Bearer sk-REPLACE-WITH-A-REAL-SECRET'
```

### Public chat completion

```bash
curl -sS https://api.sage.org.ai/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-REPLACE-WITH-A-REAL-SECRET' \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {"role": "user", "content": "reply with public-api-ok"}
    ],
    "temperature": 0,
    "max_tokens": 16
  }'
```

### Stack status

```bash
cd /home/shuhao/vllm-hust-workstation
./scripts/manage_public_stack.sh status
```

Expected result:

- local backend: ok
- local workstation: ok
- public backend: ok
- public workstation: ok

## Common Failure Mode

Symptom:

- backend `/v1/models` works with auth
- workstation `/api/models` reports `upstreamAvailable: false`

Root cause:

- deployed workstation runtime still contains the old key or `not-required`

Fix:

- run full workstation redeploy with `./scripts/deploy_workstation.sh ci-deploy`

Do not assume a service restart will refresh build-time embedded env.

## Operational Rule

Whenever the API key changes, do all three steps:

1. Update `.env`.
2. Restart backend so `VLLM_API_KEY` changes take effect.
3. Rebuild and redeploy workstation so its runtime uses the same bearer token.