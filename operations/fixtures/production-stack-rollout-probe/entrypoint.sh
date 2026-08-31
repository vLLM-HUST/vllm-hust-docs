#!/bin/sh
set -eu

# Production Stack supplies router-specific arguments. This fixture ignores
# them deliberately and exposes only a deterministic readiness endpoint.
exec httpd -f -p 8000 -h /www
