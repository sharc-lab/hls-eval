# ForgeBench base-config correctness suite

The dataset in hls_eval_data_accel/forgebench is generated from the **50 concrete
base configurations** on upstream feature/correctness-harness, pinned to commit
7f9cbd777e02c8fb050e71720673300b29b1b742. It replaces the older 45 checked-in
module/optimization kernels.

There are 14 GEMM, 29 convolution, and 7 LLM configurations. The symbolic
conv_variable.json is retained in the vendored source but excluded from the
runnable suite because it is not valid concrete JSON. The dataset's suite.json
lists every included design and the exclusion. No operator-sweep or scale-model
configs are added.

## Correctness contract

Every generated kernel uses **ap_fixed<16,5>**. Every testbench compares **every
element of every declared output** against independent Python **float64** goldens:

~~~text
abs(actual - golden) <= 1e-3
~~~

No relative-error allowance or fixed-point emulation is used in the golden.
Goldens stay double precision in the testbench. A numerical deviation above the
threshold is a failure, including quantization or overflow differences.

Each design is self-contained: top.cpp, top.h, tb_top.cpp, tb_support.h,
input .txt files, output .golden.txt files, testbench.json, config.json,
upstream_config.json, and HLS Tcl entry points. Actual output dumps use
the suffix _output.txt and never overwrite the goldens.

The comparator rejects missing, extra, malformed, and nonfinite fixture values.
Output buffers are initialized to representable values chosen to differ from
their goldens, so unwritten output elements fail. Exit codes are 0 for a pass,
1 for mismatches, and 2 for fixture/I/O errors. There is no missing-golden skip
or success fallback.

## Reproduce

Run from the repository root:

~~~bash
OPENBLAS_NUM_THREADS=2 uv run python design_gen_scripts/forgebench/generate.py
OPENBLAS_NUM_THREADS=2 uv run python design_gen_scripts/forgebench/audit_fixtures.py \
  --report design_gen_scripts/forgebench/fixture_audit.json
uv run python design_gen_scripts/forgebench/validate.py \
  --hls-include /tools/software/xilinx/ARCHIVE/Vitis_HLS/2024.1/include \
  --work-dir /tmp/forgebench-base-validation --jobs 8 --timeout 600
uv run python design_gen_scripts/forgebench/summarize.py \
  --work-dir /tmp/forgebench-base-validation
uv run pytest -q tests/test_forgebench_testbenches.py
~~~

Generation accepts repeatable --design NAME and --root for a separate
development subset. The audit requires the full suite by default; use
--allow-subset only for deliberate development subsets. Regeneration replaces
numeric fixtures in the selected design directories.

For Vitis C simulation, run vitis_hls -f dataset_csim.tcl within a design.
The run_hls.tcl entry point runs the correctness test before synthesis. Native
validation uses the actual Vitis fixed-point headers and math libraries, with
GCC bounds instrumentation. It returns nonzero for mismatches, compile/execution
errors, timeouts, missing testbenches, or missing comparison results.

## Provenance and necessary config repairs

The upstream directory contains byte-identical base JSON configs, code generators,
templates, and backend support from the pinned revision. Its provenance.json records
their SHA-256 hashes. Generation does not patch emitted C++.

Each design retains its untouched upstream_config.json. The effective
config.json forces the requested fixed-point datatype and applies five
documented config repairs needed to make complete functional tests:

- testing_impl: load the existing vector and bias ports before the scalar
  dot product.
- testing_unroll: add the same load/dot-product/store path for its declared
  but previously unwritten scalar output.
- resnet50_block3_downsample: final residual addition, activation, and store
  process all 1024 output channels rather than 512.
- resnet50_block4_downsample: the same correction for 2048 rather than 1024
  output channels.
- vec_mtx_p2: load all 64 vector elements rather than only 16.

The scalar test contract is:

~~~text
DRAM_12[0] = dot(DRAM_5[:16], DRAM_10[:16]) + DRAM_11[0]
~~~

All declared buffer and port dimensions are preserved. Every local config repair
is recorded in its testbench manifest and validation report.

The convolution configs explicitly specify output extents, sometimes beyond the
usual output-size formula. The reference preserves those extents and treats
samples outside the logical input as zero, matching the kernel's boundary
checks. This is convolution padding; oversized reads of actual model buffers
are rejected.

## Python reference and fixture coverage

The reference directory adapts the branch's independent NumPy operation models
to float64. Its provenance file lists the original source hashes and local
adaptations. The reference reads configs, not generated C++. It rejects
out-of-range buffer accesses, reads of unwritten data, incomplete output stores,
and attention groupings that leave heads uncomputed. Convolution uses vectorized
channel contractions for efficient full-size reference evaluation.

Each design has one deterministic signed input case, exactly representable at
the kernel input precision. Convolution weights are sparse across channels with
varied nonzero spatial taps; batch-normalization variances are positive.
These cases exercise full-size outputs but do not exhaust the input space.

The fixture audit checks config provenance, documented repairs, interface
dimensions, deterministic inputs, source/fixture hashes, and recomputed goldens.
A passing fixture audit establishes consistency, not numerical kernel accuracy.

See [validation_report.md](validation_report.md) for run results and limitations,
[deviations.json](deviations.json) for per-output numerical errors, and
[fixture_audit.json](fixture_audit.json) for fixture checks. Numerical deviations
can result from quantization, overflow, or remaining implementation defects.
Kernel arithmetic is retained and failures are reported.

## Validation evidence

The imported suite has **50/50 fixture audits passing**. Native fixed-point
validation found **32 passes, 14 numerical mismatches, and 4 arithmetic
exceptions**, with no reported array-bounds errors. Every design compiled.

All **50 temporary float controls pass** against the same float64 goldens at
the same absolute 1e-3 tolerance. Their input and golden hashes match the
fixed-point dataset. This cross-check supports the reference models and isolates
the remaining observed failures to the fixed-point executions. It does not
make the failing fixed-point kernels pass.

Reproduce the temporary control without modifying the fixed-point dataset:

~~~bash
uv run python design_gen_scripts/forgebench/validate_float_control.py \
  --hls-include /tools/software/xilinx/ARCHIVE/Vitis_HLS/2024.1/include \
  --work-dir /tmp/forgebench-base-float-control --jobs 8
~~~

The 30 tooling tests pass. Additional runs of compiled GEMM and convolution
fixed-point testbenches, and an LLM float-control testbench, returned 0 with valid
goldens, 1 with a corrupted golden, and 2 with a missing golden. See
[harness_negative_checks.json](harness_negative_checks.json) and
[float_control_results.json](float_control_results.json).
