import shutil
from pathlib import Path

import pytest

from hls_eval.flow_parameterization.flow_parameterization import (
    DesignSpaceExplicit,
    JinjaParamaterizationFlow,
    PreprocessorClangParamaterizationFlow,
    PreprocessorParamaterizationFlow,
)

DIR_CURRENT = Path(__file__).parent

DIR_TEST_OUTPUTS = DIR_CURRENT / "test_outputs"

DIR_TEST_DESIGN_0 = DIR_CURRENT / "test_design_0"
DIR_TEST_DESIGN_1 = DIR_CURRENT / "test_design_1"


@pytest.mark.parametrize(
    "flow_type",
    [
        PreprocessorParamaterizationFlow,
        pytest.param(
            PreprocessorClangParamaterizationFlow,
            marks=pytest.mark.skipif(
                shutil.which("clang") is None, reason="Clang unavailable"
            ),
        ),
    ],
    ids=["pcpp", "clang"],
)
def test_define_preprocessor_paramaterization_flow(flow_type):
    configs: list[dict[str, int]] = [
        {
            "SIZE": 16,
            "DATA_T_TOTAL": 16,
            "DATA_T_INT": 5,
            "DO_PIPELINE": 0,
            "PARALLEL_FACTOR": 1,
            "USE_RELU_ACTIVATION": 0,
        },
        {
            "SIZE": 32,
            "DATA_T_TOTAL": 24,
            "DATA_T_INT": 8,
            "DO_PIPELINE": 1,
            "PARALLEL_FACTOR": 4,
            "USE_RELU_ACTIVATION": 1,
        },
        {
            "SIZE": 64,
            "DATA_T_TOTAL": 32,
            "DATA_T_INT": 12,
            "DO_PIPELINE": 0,
            "PARALLEL_FACTOR": 8,
            "USE_RELU_ACTIVATION": 1,
        },
    ]
    design_space = DesignSpaceExplicit(design_space=configs)

    sources = {
        "test_design_0/vec_process.cpp": (
            DIR_TEST_DESIGN_0 / "vec_process.cpp"
        ).read_text(),
    }

    DIR_TEST = (
        DIR_TEST_OUTPUTS
        / f"test_define_preprocessor_paramaterization_flow_{flow_type.__name__}"
    )
    # make a source dir that has the original source files, so that the preprocessor can find them
    DIR_TEST.mkdir(parents=True, exist_ok=True)
    DIR_TEST_SRC = DIR_TEST / "src"
    DIR_TEST_SRC.mkdir(parents=True, exist_ok=True)
    for src_name, src_content in sources.items():
        src_path = DIR_TEST_SRC / src_name
        src_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.write_text(src_content)

    # also make a paramatrized dir
    DIR_PARAM = DIR_TEST / "param"
    DIR_PARAM.mkdir(parents=True, exist_ok=True)

    flow = flow_type()
    sources_parameterized = flow.preprocess(
        sources=sources,
        design_space=design_space,
    )

    for i, sources_i in enumerate(sources_parameterized):
        for src_name, src_content in sources_i.items():
            param_src_path = DIR_PARAM / f"version_{i}" / src_name
            param_src_path.parent.mkdir(parents=True, exist_ok=True)
            param_src_path.write_text(src_content)

    assert len(sources_parameterized) == len(configs)
    for i, (config, sources_i) in enumerate(
        zip(configs, sources_parameterized, strict=True)
    ):
        assert sources_i.keys() == sources.keys()
        print(f"Version {i}:")
        for src_name, src_content in sources_i.items():
            print(f"Source: {src_name}")
            print(src_content)

            assert "#include <ap_fixed.h>" in src_content
            assert "#line" not in src_content
            assert "#define" not in src_content
            assert (
                f"typedef ap_fixed<{config['DATA_T_TOTAL']}, {config['DATA_T_INT']}> data_t;"
                in src_content
            )
            for array in ("A", "B", "C"):
                assert f"data_t {array}[{config['SIZE']}]" in src_content
            assert f"i < {config['SIZE']}" in src_content
            assert ("#pragma HLS PIPELINE II = 1" in src_content) == bool(
                config["DO_PIPELINE"]
            )
            parallel = config["PARALLEL_FACTOR"] > 1
            assert src_content.count("#pragma HLS ARRAY_PARTITION") == (
                3 if parallel else 0
            )
            assert ("#pragma HLS UNROLL" in src_content) == parallel
            if parallel:
                normalized = " ".join(src_content.split())
                assert "#pragma HLS UNROLL factor = PARALLEL_FACTOR" in normalized
                for array in ("A", "B", "C"):
                    assert (
                        f"#pragma HLS ARRAY_PARTITION variable = {array} "
                        "dim = 1 factor = PARALLEL_FACTOR type = cyclic"
                    ) in normalized
            relu = bool(config["USE_RELU_ACTIVATION"])
            assert ("C[i] = (result > 0) ? result : data_t(0);" in src_content) == relu
            assert ("C[i] = result;" in src_content) == (not relu)


def test_jinja_paramaterization_flow():
    configs = [
        {
            "SIZE": 16,
            "DATA_T_TOTAL": 16,
            "DATA_T_INT": 5,
            "DO_PIPELINE": 0,
            "PARALLEL_FACTOR": 1,
            "USE_RELU_ACTIVATION": 0,
        },
        {
            "SIZE": 32,
            "DATA_T_TOTAL": 24,
            "DATA_T_INT": 8,
            "DO_PIPELINE": 1,
            "PARALLEL_FACTOR": 4,
            "USE_RELU_ACTIVATION": 1,
        },
        {
            "SIZE": 64,
            "DATA_T_TOTAL": 32,
            "DATA_T_INT": 12,
            "DO_PIPELINE": 0,
            "PARALLEL_FACTOR": 8,
            "USE_RELU_ACTIVATION": 1,
        },
    ]
    src_name = "test_design_1/vec_process.cpp"
    sources = {src_name: (DIR_TEST_DESIGN_1 / "vec_process.cpp").read_text()}
    output_dir = DIR_TEST_OUTPUTS / "test_jinja_paramaterization_flow"
    template_path = output_dir / "src" / src_name
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(sources[src_name])

    designs = JinjaParamaterizationFlow().preprocess(
        sources=sources, design_space=DesignSpaceExplicit(configs)
    )

    assert len(designs) == len(configs)
    for i, (config, design) in enumerate(zip(configs, designs, strict=True)):
        assert design.keys() == sources.keys()
        rendered = design[src_name]
        output_path = output_dir / "param" / f"version_{i}" / src_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
        print(f"Version {i}:\nSource: {src_name}\n{rendered}")

        assert "#include <ap_fixed.h>" in rendered
        for marker in ("{{", "}}", "{%", "%}", "#define", "#if"):
            assert marker not in rendered
        for name in config:
            assert name not in rendered
        assert (
            f"typedef ap_fixed<{config['DATA_T_TOTAL']}, {config['DATA_T_INT']}> data_t;"
            in rendered
        )
        for array in ("A", "B", "C"):
            assert f"data_t {array}[{config['SIZE']}]" in rendered
        assert f"i < {config['SIZE']}" in rendered
        assert ("#pragma HLS PIPELINE II = 1" in rendered) == bool(
            config["DO_PIPELINE"]
        )

        factor = config["PARALLEL_FACTOR"]
        assert rendered.count("#pragma HLS ARRAY_PARTITION") == (3 if factor > 1 else 0)
        assert ("#pragma HLS UNROLL" in rendered) == (factor > 1)
        if factor > 1:
            assert f"#pragma HLS UNROLL factor = {factor}" in rendered
            for array in ("A", "B", "C"):
                assert (
                    f"#pragma HLS ARRAY_PARTITION variable = {array} "
                    f"dim = 1 factor = {factor} type = cyclic"
                ) in rendered

        relu = bool(config["USE_RELU_ACTIVATION"])
        assert ("C[i] = (result > 0) ? result : data_t(0);" in rendered) == relu
        assert ("C[i] = result;" in rendered) == (not relu)
