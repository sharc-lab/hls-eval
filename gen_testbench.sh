#!/usr/bin/sh

dir_to_run=$1

if [ ! -d "$dir_to_run" ]; then
    echo "Error: Directory $dir_to_run does not exist."
    exit 1
fi

model="Qwen/Qwen2.5-Coder-32B-Instruct"
# model="meta-llama/Llama-3-70b-chat-hf"

uv run ./hls_eval/meta_hls_bench_builder_tool.py --source-bench-dir "$dir_to_run" --output-dir "$dir_to_run" --model-name $model --mode testbench
