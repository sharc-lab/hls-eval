"""Exercise the correctness gate without requiring an XLS build or model."""

import json
import hashlib
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hls_eval.eval_xls_gepa import XLSGepaConfig, XLSGepaEvaluator, _split_tests


ORIGINAL = """const W = s32:1;
pub fn idct(f: s32[1]) -> s32[1] { [f[0] + W] }
#[test]
fn original_test() { assert_eq(idct([s32:1]), [s32:2]); }
"""


class FakeXLS(XLSGepaEvaluator):
    def _tool(self, name):
        return Path(name)

    def _tool_fingerprints(self):
        return {"fake_tools": "fixed"}

    def _run(self, command, directory, label, timeout=None, required=True):
        if label == "protected_tests":
            text = (directory / "protected_tests.x").read_text()
            assert "fn original_test()" in text
            assert "fn candidate_test()" not in text
            if "s32:999" in text:
                raise RuntimeError("protected test failed")
        if label == "convert":
            return ("top fn idct(f: bits[32][1] id=1) -> bits[32][1] {\n"
                    "  ret x: bits[32][1] = array(f, id=2)\n}\n", "", {})
        if label == "opt":
            return ("top fn idct(f: bits[32][1] id=1) -> bits[32][1] {\n"
                    "  ret x: bits[32][1] = array(f, id=2)\n}\n", "", {})
        if label == "codegen":
            (directory / "design.sv").write_text("module xls_gepa_candidate; endmodule\n")
        if label in ("delay", "secondary_delay"):
            return "# Critical path:\n  40ps (fake node)\n\n", "", {"timeout": False, "returncode": 0}
        if label == "formal":
            return "", "", {"timeout": True, "returncode": None}
        return "", "", {"timeout": False, "returncode": 0}


def make_evaluator(tmp_path):
    original = tmp_path / "idct.x"
    original.write_text(ORIGINAL)
    xls = tmp_path / "xls"
    xls.mkdir()
    formal = xls / "bazel-bin/xls/dev_tools/check_ir_equivalence_main"
    formal.parent.mkdir(parents=True)
    formal.write_text("")
    return FakeXLS(original, xls, tmp_path / "work", XLSGepaConfig(top="idct"))


class XLSGepaEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.tmp_path = Path(self.temp.name)

    def test_original_and_candidate_use_same_protected_testbench(self):
        evaluator = make_evaluator(self.tmp_path)
        baseline = evaluator.evaluate()
        candidate = ORIGINAL.replace("s32:1;", "s32:1;\n// rewritten", 1) + (
            "\n#[test]\nfn candidate_test() { assert_eq(s32:0, s32:0); }\n")
        result = evaluator.evaluate(candidate)
        self.assertEqual(baseline["correctness_status"], "passed_testbench")
        self.assertEqual(result["correctness_status"], "passed_testbench")
        self.assertEqual(result["formal_status"], "inconclusive_timeout")
        self.assertEqual(result["score"], baseline["score"])
        self.assertEqual(result["score"], 1 / 41)
        config = json.loads((self.tmp_path / "work/gepa_config.json").read_text())
        self.assertEqual(config["test_count"], 1)

    def test_failing_candidate_receives_zero_score(self):
        evaluator = make_evaluator(self.tmp_path)
        result = evaluator.evaluate(ORIGINAL.replace("s32:1;", "s32:999;", 1))
        self.assertEqual(result["correctness_status"], "rejected")
        self.assertFalse(result["testbench_passed"])
        self.assertEqual(result["score"], 0)

    def test_formal_counterexample_rejects_candidate(self):
        evaluator = make_evaluator(self.tmp_path)
        original_run = evaluator._run

        def with_counterexample(command, directory, label, timeout=None, required=True):
            if label == "formal":
                return "verified not equivalent: counterexample", "", {
                    "timeout": False, "returncode": 1}
            return original_run(command, directory, label, timeout, required)

        evaluator._run = with_counterexample
        result = evaluator.evaluate(ORIGINAL + "\n// changed implementation\n")
        self.assertTrue(result["testbench_passed"])
        self.assertEqual(result["formal_status"], "proven_not_equivalent")
        self.assertEqual(result["correctness_status"], "rejected")
        self.assertEqual(result["score"], 0)

    def test_top_signature_change_is_rejected(self):
        evaluator = make_evaluator(self.tmp_path)
        result = evaluator.evaluate(ORIGINAL.replace("f: s32[1]", "f: u32[1]", 1))
        self.assertEqual(result["correctness_status"], "rejected")
        self.assertIn("top signature", result["feedback"])
        self.assertEqual(result["score"], 0)

    def test_design_without_tests_is_refused(self):
        source = self.tmp_path / "no_tests.x"
        source.write_text("pub fn idct(f: s32[1]) -> s32[1] { f }\n")
        with self.assertRaisesRegex(ValueError, "at least one"):
            XLSGepaEvaluator(source, self.tmp_path, self.tmp_path / "work",
                             XLSGepaConfig(top="idct"))

    def test_nonpublic_top_function_is_supported(self):
        source = self.tmp_path / "nonpublic.x"
        source.write_text(ORIGINAL.replace("pub fn idct", "fn idct"))
        xls = self.tmp_path / "xls"
        xls.mkdir()
        evaluator = FakeXLS(source, xls, self.tmp_path / "work",
                            XLSGepaConfig(top="idct"))
        self.assertEqual(evaluator.evaluate()["correctness_status"],
                         "passed_testbench")

    def test_bundled_idct_matches_pinned_provenance(self):
        case_dir = Path(__file__).parents[1] / "hls_eval_data/xls/idct_chen"
        provenance = json.loads((case_dir / "PROVENANCE.json").read_text())
        actual = hashlib.sha256((case_dir / "idct_chen.x").read_bytes()).hexdigest()
        self.assertEqual(actual, provenance["source_sha256"])

    def test_bundled_adler32_matches_pinned_provenance(self):
        case_dir = Path(__file__).parents[1] / "hls_eval_data/xls/adler32"
        provenance = json.loads((case_dir / "PROVENANCE.json").read_text())
        actual = hashlib.sha256((case_dir / "adler32.x").read_bytes()).hexdigest()
        self.assertEqual(actual, provenance["source_sha256"])
        manifest = json.loads((case_dir / "gepa-config.json").read_text())
        summary = json.loads((case_dir / "gepa-one-call-summary.json").read_text())
        self.assertEqual(actual, manifest["source_sha256"])
        self.assertEqual(actual, summary["baseline"]["original_source_sha256"])
        self.assertEqual(summary["model_calls"], 1)
        self.assertFalse(summary["improvement_achieved"])

    def test_published_validation_sources_match_result_hashes(self):
        repo = Path(__file__).parents[1]
        pinned = repo / "hls_eval_data/xls/idct_chen/idct_chen.x"
        original_hash = hashlib.sha256(pinned.read_bytes()).hexdigest()
        for name in ("manual-v2", "incorrect"):
            with self.subTest(name=name):
                source = (repo / "validation" / f"{name}.x").read_text(encoding="utf-8")
                implementation, _, _ = _split_tests(source)
                record = json.loads((repo / "validation" / f"{name}.json").read_text())
                self.assertEqual(hashlib.sha256(implementation.encode()).hexdigest(),
                                 record["source_sha256"])
                self.assertEqual(original_hash, record["original_source_sha256"])

    @unittest.skipUnless(importlib.util.find_spec("gepa"), "GEPA is optional")
    def test_real_gepa_adapter_with_deterministic_reflection(self):
        original = self.tmp_path / "idct.x"
        original.write_text(ORIGINAL)
        xls = self.tmp_path / "xls"
        xls.mkdir()
        evaluator = FakeXLS(original, xls, self.tmp_path / "work",
                            XLSGepaConfig(top="idct", max_model_calls=1,
                                          max_metric_calls=3,
                                          search_timeout_seconds=30))
        responses = []

        def reflect(prompt):
            responses.append(prompt)
            return "```dslx\n" + ORIGINAL.replace("s32:1;", "s32:1; // same value", 1) + "\n```"

        summary = evaluator.run_gepa(reflect)
        self.assertEqual(len(responses), 1)
        self.assertEqual(summary["model_calls"], 1)
        self.assertFalse(summary["improvement_achieved"])
        self.assertEqual(summary["best"]["correctness_status"], "passed_testbench")
        self.assertTrue((Path(summary["run_dir"]) / "summary.json").is_file())
