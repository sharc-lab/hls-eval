#!/usr/bin/env bash
set -euo pipefail

# Builds the dataflow agent image on top of the base agent image; run
# build_docker_image.sh first. The base image build is not touched.
DIR_SCRIPT=$(dirname "$(realpath "$0")")
cd "$DIR_SCRIPT"

DOCKER_BUILDKIT=1 docker build --progress=plain \
    --build-arg BASE_IMAGE="${BASE_IMAGE_NAME:-hls-eval-agent-pi}" \
    -t "${DOCKER_IMAGE_NAME_DATAFLOW:-hls-eval-agent-pi-dataflow}" \
    -f Dockerfile.dataflow . 2>&1 | tee build_dataflow.log
