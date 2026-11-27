# XLS/GEPA project status

Updated 2026-11-26. Destination: `sharc-lab/hls-eval`. HLSFactory supplies pinned DSLX designs only.

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

After the integration PR is opened, select a third design from the pinned HLSFactory commit and run its baseline, incorrect control, justified manual control if available, and a bounded one-call local GEPA search. Keep the experiment on a separate branch and record the exact source hash, tool hashes, candidate results, and model-call count. Do not claim an optimization unless a valid GEPA candidate improves the fixed score.
