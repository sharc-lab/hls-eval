#!/usr/bin/sh

dirs_to_run=$(ls -d ./hls_eval_data/chstone/df_*/)

n_jobs=2

model="meta-llama/Llama-3.3-70B-Instruct-Turbo"
# model="meta-llama/Llama-3-70b-chat-hf"

echo "$dirs_to_run" | xargs -n 1 -P "$n_jobs" -I {} uv run ./hls_eval/meta_hls_bench_builder_tool.py --source-bench-dir {} --output-dir {} --model-name $model --mode description
