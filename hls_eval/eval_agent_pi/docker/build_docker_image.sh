#!/usr/bin/env bash
set -euo pipefail

DIR_SCRIPT=$(dirname "$(realpath "$0")")
cd "$DIR_SCRIPT"

DOCKER_BUILDKIT=1 docker build --progress=plain \
    -t "${DOCKER_IMAGE_NAME:-hls-eval-agent-pi}" -f Dockerfile . 2>&1 | tee build.log
