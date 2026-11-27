# Third design: 16-element prefix sum

Source: `sharc-lab/HLSFactory` at commit
`2aba8756de8e2fab1d1095b2483cfa695bf3be10`, path
`hlsfactory/hls_dataset_sources/xls_upstream/prefix_sum/prefix_sum.x`.
The exact pinned file has SHA256
`0efea30f3f7b8a78cad163be6ee99d3b5aa0a31716fe343c83537b40e92252bd`.
HLSFactory's provenance names XLS commit `998cf6aec2a7b09c9ad14c492fe4fca63f831fb2`
as its earlier upstream source. This experiment uses the pinned HLSFactory bytes.
The top is `prefix_sum`; the original file has one `#[test]` function with two
assertions. It computes a Hillis-Steele prefix sum across sixteen `u16` values.

## Reproduce in the existing containers

From the HLS-Eval third-design worktree root on Windows, copy the evaluator and
the pinned design into a fresh directory in `xls-gepa-work`:

```powershell
docker exec xls-gepa-work mkdir -p /tmp/hls-eval-prefix-sum/hls_eval /tmp/hls-eval-prefix-sum/hls_eval_experiments/xls_gepa_idct /tmp/hls-eval-prefix-sum/hls_eval_data/xls/prefix_sum
docker cp hls_eval/eval_xls_gepa.py xls-gepa-work:/tmp/hls-eval-prefix-sum/hls_eval/eval_xls_gepa.py
docker cp hls_eval_experiments/xls_gepa_idct/run_xls_gepa.py xls-gepa-work:/tmp/hls-eval-prefix-sum/hls_eval_experiments/xls_gepa_idct/run_xls_gepa.py
docker cp hls_eval_data/xls/prefix_sum/. xls-gepa-work:/tmp/hls-eval-prefix-sum/hls_eval_data/xls/prefix_sum/
```

The runner can then be called inside the container from
`/tmp/hls-eval-prefix-sum`. The baseline, incorrect control, manual control,
and GEPA run all use the same source, XLS root, and work directory. Use a fresh
work directory if any source, evaluator, tool, or configuration hash changes.

```bash
export PYTHONPATH=/workspace/vendor/gepa/src
cd /tmp/hls-eval-prefix-sum
COMMON='--source hls_eval_data/xls/prefix_sum/prefix_sum.x --top prefix_sum --xls-root /home/xls-developer/xls --work-dir /tmp/hls-eval-prefix-sum-runs --max-model-calls 2'
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa $COMMON
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa $COMMON --candidate hls_eval_data/xls/prefix_sum/incorrect.x
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa $COMMON --candidate hls_eval_data/xls/prefix_sum/manual-equivalent.x
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa $COMMON --run-gepa --model qwen2.5-coder:3b --ollama-url http://host.docker.internal:11434
```

XLS is at commit `0a7c502ccaaa650cb2da1929c536c4ab100eafda`; the six tool
hashes and all fixed XLS settings are in `results/config.json`. The configured
score is `1 / (1 + unit-model critical path)`. The ASAP7 estimate is secondary.
The manual variant reverses the branch condition and replaces `std::flog2(16)`
with `4`; it should preserve the function for every input. The incorrect
variant subtracts instead of adding. Both candidates omit imports because the
evaluator supplies the original pinned `import std;` during compilation. GEPA
can edit DSLX implementation text only; tests, imports, XLS flags, and model
budget are fixed.

## Recorded results

| Run | Protected test | Formal status | Unit path | ASAP7 estimate | Optimized IR nodes | Score |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Baseline | pass | `not_run` | 7 | 1420 ps | 82 | 0.125 |
| Incorrect subtraction | fail | `not_run` | — | — | — | 0 |
| Manual equivalent | pass | `proven_equivalent` | 7 | 1420 ps | 82 | 0.125 |
| GEPA seed (original implementation without import) | pass | `proven_equivalent` | 7 | 1420 ps | 82 | 0.125 |
| GEPA proposal 1 | parse error | `not_run` | — | — | — | 0 |
| GEPA proposal 2 | parse error | `not_run` | — | — | — | 0 |

The final GEPA run used two local model calls and returned the seed as best.
Its best source hash is
`a1d30b904b70dd2958e599351ddbaf99cfde354703641a9f7af376ad7ab4e7c3`.
No valid GEPA-generated candidate improved the score. Formal checking was not
run on the baseline or candidates rejected by protected tests or parsing;
these `not_run` results are not equivalence findings. No formal timeout or
inconclusive result occurred in the final run. The protected test is limited
to its two original assertions; the manual control's equivalence result is
the stronger evidence for that rewrite. XLS delay and node figures are
estimates, not placed and routed hardware measurements.

The `results/` directory preserves the config fingerprint, each result, GEPA
log, GEPA summary, and selected best source in `gepa-result.json`. An earlier three-call attempt
revealed that GEPA's seed wrongly included `import std;` and scored zero under
candidate validation. The evaluator fix pins original imports outside the
model-editable text. The recorded two-call run is the valid experiment.
