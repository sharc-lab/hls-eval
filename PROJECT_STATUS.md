# XLS/GEPA project status

Updated 2026-11-26. Destination: `sharc-lab/hls-eval`. HLSFactory supplies pinned DSLX designs only.

## Third design: prefix sum

- PR #12 was verified open against `main`, head `charith/xls-gepa-main-integration` at `549c797`, and unmerged. This work is on the separate `charith/xls-gepa-third-design` branch based on that head.
- Selected the nontrivial 16-element Hillis-Steele prefix sum with a clear `prefix_sum` top and one original test function containing two assertions. The source is pinned to HLSFactory commit `2aba8756de8e2fab1d1095b2483cfa695bf3be10`, SHA256 `0efea30f3f7b8a78cad163be6ee99d3b5aa0a31716fe343c83537b40e92252bd`.
- The evaluator now keeps original imports pinned outside GEPA's editable DSLX implementation. This fixed a zero-scoring seed discovered in an initial three-call attempt. The final run used two local `qwen2.5-coder:3b` calls with unchanged XLS settings. Twelve focused tests passed.
- Baseline: protected test passed, score 0.125, unit path 7, ASAP7 estimate 1420 ps, 82 optimized IR nodes; formal `not_run`. Incorrect subtraction: protected test failed, score zero. Manual equivalent rewrite: protected test passed, formal `proven_equivalent`, score 0.125, same estimates. GEPA's seed passed and was formally equivalent, but both generated proposals failed DSLX parsing and scored zero. No valid GEPA-generated improvement was found.
- Reproduction commands, full provenance, tool fingerprints, and saved records are in `hls_eval_data/xls/prefix_sum/README.md` and `results/`. Formal was not run for the baseline or rejected proposals; no final-run formal result was inconclusive.

## Integration

- GitHub `main` is `e31f731` and contains PR #9. PR #10 merged into `charith/xls-gepa-evaluator`; PR #11 merged into `charith/xls-gepa-artifact-verification`. That stacked branch is `cb5622e`. Neither #10 nor #11 reached `main` as of this check.
- `charith/xls-gepa-main-integration` starts at `e31f731` and cherry-picks only `1ae74a8`, `f17fa2e`, and `c67cfde`. Its file tree matches `cb5622e` before the line-ending rule and this status file. The original sparse checkout's apparent deletions were not staged.
- `.gitattributes` forces LF checkout for the pinned and validation `.x` files. Without it, a Windows checkout changed their byte hashes and four provenance checks failed. With it, all ten focused tests pass.

## Reproduced evidence

Commands were run in the preserved `xls-gepa-work` container with the integration tree copied to `/tmp/hls-eval-integration`; XLS root is `/home/xls-developer/xls` at commit `0a7c502ccaaa650cb2da1929c536c4ab100eafda`. The six exact XLS tool SHA256 values are in `hls_eval_data/xls/adler32/gepa-config.json`; a fresh `sha256sum` of all six binaries matched them. No XLS rebuild was needed. Ollama container `xls-gepa-ollama` is running. Python is 3.10.12. GEPA was imported from `/workspace/vendor/gepa/src` for the full test run.

```bash
PYTHONPATH=/workspace/vendor/gepa/src python3 -m unittest tests.test_eval_xls_gepa -v
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa --source hls_eval_data/xls/idct_chen/idct_chen.x --top idct --xls-root /home/xls-developer/xls --work-dir /tmp/hls-eval-integration-runs/idct-baseline
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa --source hls_eval_data/xls/adler32/adler32.x --top main --xls-root /home/xls-developer/xls --work-dir /tmp/hls-eval-integration-runs/adler32-baseline
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa --source hls_eval_data/xls/idct_chen/idct_chen.x --top idct --xls-root /home/xls-developer/xls --work-dir /tmp/hls-eval-integration-runs/idct-baseline --candidate validation/manual-v2.x
python3 -m hls_eval_experiments.xls_gepa_idct.run_xls_gepa --source hls_eval_data/xls/idct_chen/idct_chen.x --top idct --xls-root /home/xls-developer/xls --work-dir /tmp/hls-eval-integration-runs/idct-baseline --candidate validation/incorrect.x
```

| Design/run | Source SHA256 | Protected tests | Formal | Unit path | ASAP7 estimate | IR nodes | Score |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| IDCT baseline | `1166b8a58483a166550de600e1d910c3b12c253682ba0fc5156ae17e637cbced` | 5 pass | not run | 40 | 8488 ps | 1883 | 0.0243902439 |
| IDCT manual control | `a7cf773fa9498b0ce50120b9a175e903372cca7333351ba6cdd565d9b01683bc` implementation | 5 pass | proven equivalent | 40 | 8424 ps | 1820 | 0.0243902439 |
| IDCT incorrect control | `aa9c56e07cd8204a95bcfd410eab342a9ff1ad7d9cfff4630bfe4bcd3e318404` implementation | 5 fail | not run | — | — | — | 0 |
| Adler32 baseline | `8643a8d99c830652df6ace6015b424ee8027019e357eec5d175863f8a464684c` | 1 test function passes (6 assertions) | not run | 3 | 224 ps | 6 | 0.25 |

Both pinned source files match the SHA256 values in their HLSFactory provenance records, which pin commit `2aba8756de8e2fab1d1095b2483cfa695bf3be10`. Baseline formal status `not_run` is expected; the candidate is the subject of equivalence checking. The saved Adler32 GEPA result records one model call, formal equivalence, and no score improvement. The integration checks above made zero model calls. Unit delay and ASAP7 are XLS estimates, not placed-and-routed measurements.

## Next command

Review the focused third-design PR against PR #12's integration branch. Do not merge either PR from this experiment. A future search can improve the candidate prompt or model, but must keep the source and XLS settings pinned and report only valid score gains.
