# HLS-Eval

HLS-Eval is a benchmark and evaluation framework for LLMs on high-level synthesis (HLS) design tasks, including HLS code generation and HLS code editing. It provides a comprehensive benchmark set of HLS designs with natural language descriptions, testbenches, and reference HLS implementations. HLS-Eval also includes an evaluation framework that can run evaluations across tasks and models in a parallel and efficient manner. The framework is implemented in Python and can be easily extended to support new tasks, benchmark designs, models, and inference methods.

## Install

Using uv:

```bash
uv add git+https://github.com/sharc-lab/hls-eval.git
```

Using pip:

```bash
pip install git+https://github.com/sharc-lab/hls-eval.git
```

If cloning the repository:

```bash
git clone git@github.com:sharc-lab/hls-eval.git
cd hls-eval
uv sync
```

## Benchmark contracts

Version 2 Vitis results record `benchmark_contract_version = 2`. The revised
fixtures include numerical and output-contract changes. Compare scores within
the same contract version and scored design cohort. A case's `[comparison]`
table selects its trusted self-checking testbench or complete reference-output
comparison. An undeclared policy leaves functional correctness unverified.

The version 2 zero-shot editing task accepts the edited kernel implementation
under its original filename. Preserve the public signature and put fixed-point
conversions inside the kernel. The original headers, testbench and input data
are used for grading. The evaluator also reads legacy three-file responses
and takes only the implementation from them.

## Citation

This work was presented at the ICLAD 2025 conference. If you use HLS-Eval in your research, please cite the following paper:

```text
S. Abi-Karam and C. Hao, "HLS-Eval: A Benchmark and Framework for Evaluating LLMs on High-Level Synthesis Design Tasks," 2025 IEEE International Conference on LLM-Aided Design (ICLAD), Stanford, CA, USA, 2025, pp. 219-226, doi: 10.1109/ICLAD65226.2025.00021.
```

```bibtex
@inproceedings{hlseval,
  author={Abi-Karam, Stefan and Hao, Cong},
  booktitle={2025 IEEE International Conference on LLM-Aided Design (ICLAD)}, 
  title={HLS-Eval: A Benchmark and Framework for Evaluating LLMs on High-Level Synthesis Design Tasks}, 
  year={2025},
  doi={10.1109/ICLAD65226.2025.00021}}
```
