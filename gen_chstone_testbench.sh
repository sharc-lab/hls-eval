#!/usr/bin/sh

dirs_to_run=$(ls -d ./hls_eval_data/chstone/*/)

# filter dirs that only start with "df_"
dirs_to_run=$(echo "$dirs_to_run" | grep "df_")

n_jobs=1

model="Qwen/Qwen2.5-Coder-32B-Instruct"
# model="meta-llama/Llama-3-70b-chat-hf"

echo "$dirs_to_run" | xargs -n 1 -P "$n_jobs" -I {} uv run ./hls_eval/meta_hls_bench_builder_tool.py --source-bench-dir {} --output-dir {} --model-name $model --mode testbench
