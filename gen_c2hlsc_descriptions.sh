#!/usr/bin/sh

# dirs_to_run=$(ls -d ./hls_eval_data/c2hlsc/*/)

designs_to_run="block cusums monobit overlapping runs"

dirs_to_run=$(for design in $designs_to_run; do echo "./hls_eval_data/c2hlsc/$design/"; done)

n_jobs=2

# model="meta-llama/Llama-3.3-70B-Instruct-Turbo"
# model="meta-llama/Llama-3-70b-chat-hf"
model="Qwen/Qwen2.5-Coder-32B-Instruct"

echo "$dirs_to_run" | xargs -n 1 -P "$n_jobs" -I {} uv run ./hls_eval/meta_hls_bench_builder_tool.py --source-bench-dir {} --output-dir {} --model-name $model --mode description
