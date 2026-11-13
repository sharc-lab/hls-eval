"""Run the XLS test-bench evaluator, optionally followed by local GEPA search."""

import argparse
import json
import urllib.request
from pathlib import Path

from hls_eval.eval_xls_gepa import XLSGepaConfig, XLSGepaEvaluator


class OllamaReflection:
    """Local GEPA reflection model; the evaluator enforces the call limit."""

    def __init__(self, model: str, url: str, timeout_seconds: int):
        self.model = model
        self.url = url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def __call__(self, prompt):
        messages = ([{"role": "user", "content": prompt}]
                    if isinstance(prompt, str) else prompt)
        request = urllib.request.Request(
            self.url + "/api/chat",
            data=json.dumps({"model": self.model, "messages": messages,
                             "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.load(response)
        content = payload.get("message", {}).get("content", "")
        if not content or payload.get("done_reason") == "length":
            raise RuntimeError("Ollama returned an empty or truncated response")
        return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path,
                        help="Original DSLX design with at least one #[test]")
    parser.add_argument("--top", required=True, help="DSLX top function")
    parser.add_argument("--xls-root", required=True, type=Path,
                        help="XLS source tree with built bazel-bin tools")
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--candidate", type=Path,
                        help="Evaluate one DSLX variant against the original bench")
    parser.add_argument("--run-gepa", action="store_true",
                        help="Run a bounded search after the baseline passes")
    parser.add_argument("--model", help="Local Ollama model name for --run-gepa")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--max-model-calls", type=int, default=2)
    parser.add_argument("--request-timeout-seconds", type=int, default=300)
    args = parser.parse_args()
    if args.run_gepa and not args.model:
        parser.error("--model is required with --run-gepa")
    if args.run_gepa and args.candidate:
        parser.error("--candidate and --run-gepa are separate modes")
    evaluator = XLSGepaEvaluator(
        args.source, args.xls_root, args.work_dir,
        XLSGepaConfig(top=args.top, max_model_calls=args.max_model_calls),
    )
    baseline = evaluator.evaluate()
    if args.run_gepa:
        summary = evaluator.run_gepa(OllamaReflection(
            args.model, args.ollama_url, args.request_timeout_seconds))
        print(json.dumps(summary, indent=2))
    elif args.candidate:
        print(json.dumps(evaluator.evaluate(args.candidate.read_text()), indent=2))
    else:
        print(json.dumps(baseline, indent=2))


if __name__ == "__main__":
    main()
