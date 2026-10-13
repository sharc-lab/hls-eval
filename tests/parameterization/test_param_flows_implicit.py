from pathlib import Path

import pytest
from jinja2.exceptions import UndefinedError

from hls_eval.flow_parameterization.flow_parameterization_implicit import (
    DesignSpaceExplicit,
    DesignSpaceImplicit,
    JinjaParamaterizationFlow,
    PreprocessorParamaterizationFlow,
    convert_design_space_implicit_to_explicit,
)

DIR_CURRENT = Path(__file__).parent

DIR_TEST_OUTPUTS = DIR_CURRENT / "test_outputs"

DIR_TEST_DESIGN_0 = DIR_CURRENT / "test_design_0"
DIR_TEST_DESIGN_1 = DIR_CURRENT / "test_design_1"

PARAMETERS = {
    "SIZE": [16, 32],
    "DATA_T_TOTAL": [16, 24],
    "DATA_T_INT": [8, 16],
    "DO_PIPELINE": [False, True],
    "PARALLEL_FACTOR": [1, 4],
    "USE_RELU_ACTIVATION": [False, True],
}
CONSTRAINTS = ["DATA_T_INT < DATA_T_TOTAL"]


def test_implicit_expands_to_cartesian_product():
    implicit = DesignSpaceImplicit({"A": [1, 2, 3], "B": [False, True]})
    explicit = convert_design_space_implicit_to_explicit(implicit)

    assert implicit.size_unconstrained() == 6
    assert explicit.design_space == [
        {"A": 1, "B": False},
        {"A": 1, "B": True},
        {"A": 2, "B": False},
        {"A": 2, "B": True},
        {"A": 3, "B": False},
        {"A": 3, "B": True},
    ]


def test_implicit_constraints_filter_points():
    implicit = DesignSpaceImplicit(PARAMETERS, CONSTRAINTS)
    explicit = convert_design_space_implicit_to_explicit(implicit)

    assert implicit.size_unconstrained() == 64
    # DATA_T_INT=16 with DATA_T_TOTAL=16 is the one excluded pair out of four.
    assert len(explicit.design_space) == 48
    assert all(p["DATA_T_INT"] < p["DATA_T_TOTAL"] for p in explicit.design_space)


def test_implicit_constraint_with_unknown_name_raises():
    implicit = DesignSpaceImplicit({"A": [1, 2]}, ["A < MISSING"])
    with pytest.raises(UndefinedError):
        convert_design_space_implicit_to_explicit(implicit)


def test_implicit_sampling_is_capped_and_reproducible():
    implicit = DesignSpaceImplicit(PARAMETERS, CONSTRAINTS)
    full = convert_design_space_implicit_to_explicit(implicit).design_space

    sampled = convert_design_space_implicit_to_explicit(implicit, max_points=5)
    again = convert_design_space_implicit_to_explicit(implicit, max_points=5)
    other_seed = convert_design_space_implicit_to_explicit(
        implicit, max_points=5, seed=7
    )

    assert len(sampled.design_space) == 5
    assert sampled.design_space == again.design_space
    assert sampled.design_space != other_seed.design_space
    assert all(point in full for point in sampled.design_space)
    # A cap above the space size keeps every point.
    assert (
        convert_design_space_implicit_to_explicit(implicit, max_points=1000).design_space
        == full
    )


def test_implicit_json_round_trip():
    implicit = DesignSpaceImplicit(PARAMETERS, CONSTRAINTS)
    parsed = DesignSpaceImplicit()
    parsed.parse_from_json(implicit.render_to_json())

    assert parsed.parameters == PARAMETERS
    assert parsed.constraints == CONSTRAINTS


@pytest.mark.parametrize(
    ("parameters", "error"),
    [
        ({"A": []}, TypeError),
        ({"A": 4}, TypeError),
        ({"A": [[1]]}, TypeError),
        ({"A": [1, 1]}, ValueError),
    ],
    ids=["empty", "not_a_list", "non_scalar", "duplicate"],
)
def test_implicit_type_check_rejects_bad_parameters(parameters, error):
    with pytest.raises(error):
        DesignSpaceImplicit(parameters)


def test_jinja_flow_accepts_implicit_and_explicit():
    src_name = "test_design_1/vec_process.cpp"
    sources = {src_name: (DIR_TEST_DESIGN_1 / "vec_process.cpp").read_text()}
    implicit = DesignSpaceImplicit(PARAMETERS, CONSTRAINTS)
    explicit = convert_design_space_implicit_to_explicit(implicit)
    flow = JinjaParamaterizationFlow(strict_undefined=True)

    designs = flow.preprocess(sources, implicit)

    assert designs == flow.preprocess(sources, explicit)
    assert len(designs) == 48

    output_dir = DIR_TEST_OUTPUTS / "test_jinja_flow_accepts_implicit_and_explicit"
    (output_dir / "design_space_implicit.json").parent.mkdir(parents=True, exist_ok=True)
    (output_dir / "design_space_implicit.json").write_text(implicit.render_to_json())
    (output_dir / "design_space_explicit.jsonl").write_text(explicit.render_to_jsonl())

    for i, (point, design) in enumerate(zip(explicit.design_space, designs, strict=True)):
        rendered = design[src_name]
        output_path = output_dir / "param" / f"version_{i}" / src_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)

        for marker in ("{{", "}}", "{%", "%}"):
            assert marker not in rendered
        assert (
            f"typedef ap_fixed<{point['DATA_T_TOTAL']}, {point['DATA_T_INT']}> data_t;"
            in rendered
        )
        assert f"i < {point['SIZE']}" in rendered
        assert ("#pragma HLS PIPELINE II = 1" in rendered) == point["DO_PIPELINE"]
        factor = point["PARALLEL_FACTOR"]
        assert ("#pragma HLS UNROLL" in rendered) == (factor > 1)
        if factor > 1:
            assert f"#pragma HLS UNROLL factor = {factor}" in rendered


def test_preprocessor_flow_accepts_implicit():
    src_name = "test_design_0/vec_process.cpp"
    sources = {src_name: (DIR_TEST_DESIGN_0 / "vec_process.cpp").read_text()}
    implicit = DesignSpaceImplicit({"SIZE": [16, 64], "DO_PIPELINE": [0, 1]})

    designs = PreprocessorParamaterizationFlow().preprocess(sources, implicit)

    assert len(designs) == 4
    points = convert_design_space_implicit_to_explicit(implicit).design_space
    for point, design in zip(points, designs, strict=True):
        assert f"i < {point['SIZE']}" in design[src_name]
        assert ("#pragma HLS PIPELINE II = 1" in design[src_name]) == bool(
            point["DO_PIPELINE"]
        )


def test_explicit_design_space_still_works():
    src_name = "test_design_1/vec_process.cpp"
    sources = {src_name: (DIR_TEST_DESIGN_1 / "vec_process.cpp").read_text()}
    point = {
        "SIZE": 32,
        "DATA_T_TOTAL": 24,
        "DATA_T_INT": 8,
        "DO_PIPELINE": True,
        "PARALLEL_FACTOR": 4,
        "USE_RELU_ACTIVATION": True,
    }

    designs = JinjaParamaterizationFlow().preprocess(
        sources, DesignSpaceExplicit([point])
    )

    assert len(designs) == 1
    assert "typedef ap_fixed<24, 8> data_t;" in designs[0][src_name]
