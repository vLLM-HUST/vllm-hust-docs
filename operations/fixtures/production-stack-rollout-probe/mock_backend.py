from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


MODEL = "vllmhust-e2e-model"


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict[str, object]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok", "backend": "vllmhust-e2e"})
        elif self.path == "/v1/models":
            self._send(
                200,
                {"object": "list", "data": [{"id": MODEL, "object": "model"}]},
            )
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        request = json.loads(self.rfile.read(length) or b"{}")
        if self.path not in {"/v1/completions", "/v1/chat/completions"}:
            self._send(404, {"error": "not found"})
            return

        # A small deterministic CPU workload makes Metrics API driven HPA tests
        # observable without a model or accelerator.
        deadline = time.process_time() + 0.01
        value = 0
        while time.process_time() < deadline:
            value = (value * 33 + 17) % 1_000_003

        if self.path == "/v1/chat/completions":
            choices = [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "forwarded-by-vllmhust-e2e",
                    },
                    "finish_reason": "stop",
                }
            ]
            object_name = "chat.completion"
        else:
            choices = [
                {
                    "index": 0,
                    "text": "forwarded-by-vllmhust-e2e",
                    "finish_reason": "stop",
                }
            ]
            object_name = "text_completion"

        self._send(
            200,
            {
                "id": "cmpl-vllmhust-e2e",
                "object": object_name,
                "model": request.get("model", MODEL),
                "backend": "vllmhust-e2e",
                "work": value,
                "choices": choices,
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )

    def log_message(self, format: str, *args: object) -> None:
        print(f"backend_request {self.command} {self.path} " + format % args, flush=True)


ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
