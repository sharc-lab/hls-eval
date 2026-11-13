# XLS GEPA evaluator validation (2026-11-12)

The new module was exercised in the preserved XLS Docker container against
the pinned HLSFactory IDCT design. The container used Python 3.10.12 and the
previously built XLS tools. HLS-Eval itself declares Python 3.12 or newer;
the isolated module also ran under 3.10 for this check. No XLS rebuild or
external model call was needed for the evaluator checks.

## Automated tests

With pinned GEPA importable,
`python3 -m unittest discover -s tests -p test_eval_xls_gepa.py -v` passed
all eight tests. They cover pinned source provenance, rejection of a design
without tests, original and candidate use of the same protected bench,
test-bench failure, formal counterexample rejection, and top-signature
changes, published candidate source hashes, and one deterministic GEPA search
through the real GEPA API. The GEPA test uses a local callback and makes no
external model request; it skips when GEPA is not installed. The evaluator
tests use a fake XLS command runner; the checks below use the real built XLS
tools.

## Real XLS results

| Design | Protected tests | Formal result | Unit path | ASAP7 estimate | IR nodes | Score |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Pinned original | 5 passed | Not run (baseline) | 40 | 8488 ps | 1883 | 0.0243902439 |
| Manual rewrite v2 | 5 passed | Proven equivalent to original | 40 | 8424 ps | 1820 | 0.0243902439 |
| Deliberately incorrect rewrite | Failed | Not run | — | — | — | 0 |

The original and manual rewrite values match the earlier standalone
experiment's estimates. The new integration's correctness gate uses the
original DSLX test bench. It does not run the earlier 527-input differential
suite; that earlier suite and its results remain separate evidence.

Saved evaluator records: `baseline.json`, `manual-v2.json`, and
`incorrect.json` in this directory. The exact candidate source files are
`manual-v2.x` and `incorrect.x`. The artifact test in
`tests/test_eval_xls_gepa.py` verifies their implementation hashes against
the saved evaluator records and the pinned original source hash. Rerunning
XLS is still required to reproduce the measurements and correctness outcomes.

## Bounded GEPA check

The local `qwen2.5-coder:3b` model was called once through the new GEPA
adapter, with a 180-second request timeout and a one-call budget. The model
request timed out before proposing a candidate. GEPA retained the original
baseline, and no objective improvement was achieved. The run summary and
the GEPA log are saved here. The evaluator was subsequently changed to record
model errors explicitly in future summaries; this one-call run predates that
small logging change.

These results are XLS estimates, not measured FPGA timing or area.
