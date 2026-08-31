#!/bin/sh
set -eu

# Production Stack supplies Router/Controller-specific arguments. This fixture
# ignores them deliberately and exposes only deterministic readiness endpoints.
httpd -p 8081 -h /www
exec httpd -f -p 8000 -h /www
