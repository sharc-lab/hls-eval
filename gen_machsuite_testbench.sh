#!/usr/bin/sh

kernels_to_run="aes_aes"

dirs_to_run=$(ls -d ./hls_eval_data/machsuite/*/)

dirs_to_run_filtered=""
for line in $dirs_to_run; do
    for kernel in $kernels_to_run; do
        if echo "$line" | grep -q "$kernel"; then
            if [ -z "$dirs_to_run_filtered" ]; then
                dirs_to_run_filtered="$line"
            else
                dirs_to_run_filtered="$dirs_to_run_filtered\n$line"
            fi
        fi
    done
done

n_jobs=4

model="Qwen/Qwen2.5-Coder-32B-Instruct"

echo "$dirs_to_run_filtered" | xargs -n 1 -P "$n_jobs" -I {} uv run ./hls_eval/meta_hls_bench_builder_tool.py --source-bench-dir {} --output-dir {} --model-name "$model" --mode testbench --use-existing-description
