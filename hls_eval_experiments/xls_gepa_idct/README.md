# XLS GEPA evaluator (first design)

This module adds a DSLX source-editing evaluation path to HLS-Eval. It uses the
original design's `#[test]` functions as a protected test bench. Both the
original and each proposed implementation must pass that same bench. The
existing C/C++ Vitis benchmark and evaluator paths are unaffected.

The initial target is the pinned HLSFactory
`xls_upstream/idct_chen/idct_chen.x`, included at
`hls_eval_data/xls/idct_chen/idct_chen.x` with its source provenance.
`XLSGepaEvaluator` accepts another `.x` design when it has a top function and
at least one `#[test]` function. A fresh work directory is created for each
design and configuration; the evaluator refuses to reuse a directory whose
source or configuration differs.

## Requirements

- HLS-Eval's Python environment (Python 3.12 or newer).
- An XLS checkout with built `interpreter_main`, `ir_converter_main`,
  `opt_main`, `codegen_main`, and `delay_info_main` in `bazel-bin`.
- For search only: GEPA installed in that Python environment and a local
  Ollama server with the requested model. The equivalence checker is optional.

From the HLS-Eval repository root, run a baseline first:

```bash
python -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa \
  --source hls_eval_data/xls/idct_chen/idct_chen.x \
  --top idct \
  --xls-root /path/to/xls \
  --work-dir /path/to/output/xls-gepa-idct
```

Run a bounded local GEPA search after the baseline passes:

```bash
python -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa \
  --source hls_eval_data/xls/idct_chen/idct_chen.x \
  --top idct \
  --xls-root /path/to/xls \
  --work-dir /path/to/output/xls-gepa-idct \
  --run-gepa --model qwen2.5-coder:3b --max-model-calls 2
```

When the evaluator runs inside Docker and Ollama runs in another local
container, add `--ollama-url http://host.docker.internal:11434` if Ollama is
published on the host at that port.

To evaluate one modified `.x` file without calling a model, use the baseline
command with `--candidate /path/to/modified.x`. The original protected tests
are used for the candidate regardless of any tests in that modified file.
The exact manual rewrite and deliberately incorrect control used for the
published results are included at `validation/manual-v2.x` and
`validation/incorrect.x`. For example, add `--candidate validation/manual-v2.x`
to the baseline command to rerun the manual control. The artifact test checks
that these source files match the SHA256 hashes in their saved result records;
it does not rerun XLS.

The work directory stores `gepa_config.json`, original and candidate sources,
the protected bench, XLS command output and arguments, per-candidate
`result.json` files, and GEPA summaries. Candidate-supplied tests are removed;
the original tests are appended instead. The original design must pass before
a candidate is scored. A failed test, interface change, or codegen failure
rejects a candidate with score zero.

The fixed score is `1 / (1 + critical_path_unit_delay)` for candidates that
pass the bench. The unit delay is an abstract XLS estimate. A secondary ASAP7
estimate is recorded when available and does not change the score. Formal
equivalence against the original is recorded when the tool is available: a
counterexample rejects the candidate, while timeout or tool failure is
inconclusive. Bench passage is not proof of equivalence for all inputs or of
correctness against an independent mathematical specification. Generated RTL
is not placed and routed hardware.

This first integration intentionally uses the original DSLX tests rather than
HLS-Eval's C/C++ `BenchmarkCase`, which requires a C/C++ test bench and Vitis.
Broader benchmark selection and additional comparison baselines can follow
after the first design runs end to end in the shared environment.
