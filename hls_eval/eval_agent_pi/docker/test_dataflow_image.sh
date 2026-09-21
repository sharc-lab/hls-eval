#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(realpath "$0")")/../../.."
exec uv run python -m hls_eval.eval_agent_pi.docker.test_dataflow_image "$@"
