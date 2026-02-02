#!/usr/bin/sh

dirs_to_run=$(ls -d ./hls_eval_data/polybench/*/)

n_jobs=4

echo "$dirs_to_run" | xargs -n 1 -P "$n_jobs" -I {} uv run ./hls_eval/meta_hls_bench_builder_tool.py --source-bench-dir {} --output-dir {} --model-name meta-llama/Llama-3-70b-chat-hf --mode description --use-existing-description
