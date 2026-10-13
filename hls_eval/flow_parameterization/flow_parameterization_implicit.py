from __future__ import annotations

import itertools
import json
import math
import random
import re
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from jinja2 import StrictUndefined, Template, Undefined
from jinja2.sandbox import SandboxedEnvironment
from pcpp import CmdPreprocessor

T_design_space_key = str
T_design_space_value = str | int | float | bool
T_design_space_point = dict[T_design_space_key, T_design_space_value]


class DesignSpaceExplicit:
    def __init__(self, design_space: list[T_design_space_point] | None = None):
        if design_space is None:
            self.design_space: list[T_design_space_point] = []
        else:
            self.design_space: list[T_design_space_point] = design_space
            self.type_check_design_space()

    def render_to_json(self) -> str:
        self.type_check_design_space()
        return json.dumps(self.design_space, indent=4)

    def render_to_jsonl(self) -> str:
        self.type_check_design_space()
        return "\n".join(json.dumps(point) for point in self.design_space)

    def parse_from_json(self, txt_json: str):
        self.design_space = json.loads(txt_json)
        self.type_check_design_space()

    def parse_from_jsonl(self, txt_jsonl: str):
        self.design_space = [json.loads(line) for line in txt_jsonl.splitlines()]
        self.type_check_design_space()

    def type_check_design_space(self):
        for point in self.design_space:
            if not isinstance(point, dict):
                raise TypeError(f"Design space point must be a dict, got {type(point)}")
            for key, value in point.items():
                if not isinstance(key, str):
                    raise TypeError(f"Design space key must be a str, got {type(key)}")
                if not isinstance(value, (str, int, float, bool)):
                    raise TypeError(
                        f"Design space value must be str, int, float, or bool, got {type(value)}"
                    )


class DesignSpaceImplicit:
    """Allowed values per parameter; the points are every combination of them.

    Constraints are Jinja expressions over the parameter names, e.g.
    "DATA_T_INT < DATA_T_TOTAL". A combination is kept only if all are truthy.
    """

    def __init__(
        self,
        parameters: dict[T_design_space_key, list[T_design_space_value]] | None = None,
        constraints: list[str] | None = None,
    ):
        self.parameters: dict[T_design_space_key, list[T_design_space_value]] = (
            parameters or {}
        )
        self.constraints: list[str] = constraints or []
        self.type_check_design_space()

    def render_to_json(self) -> str:
        self.type_check_design_space()
        return json.dumps(
            {"parameters": self.parameters, "constraints": self.constraints}, indent=4
        )

    def parse_from_json(self, txt_json: str):
        data = json.loads(txt_json)
        if not isinstance(data, dict) or not isinstance(data.get("parameters"), dict):
            raise TypeError('Implicit design space must be an object with "parameters"')
        self.parameters = data["parameters"]
        self.constraints = data.get("constraints", [])
        self.type_check_design_space()

    def type_check_design_space(self):
        for key, values in self.parameters.items():
            if not isinstance(key, str):
                raise TypeError(f"Design space key must be a str, got {type(key)}")
            if not isinstance(values, list) or not values:
                raise TypeError(f"Parameter {key} must have a non-empty list of values")
            for value in values:
                if not isinstance(value, (str, int, float, bool)):
                    raise TypeError(
                        f"Design space value must be str, int, float, or bool, got {type(value)}"
                    )
            if len({json.dumps(value) for value in values}) != len(values):
                raise ValueError(f"Parameter {key} has duplicate values")
        if not isinstance(self.constraints, list) or not all(
            isinstance(constraint, str) for constraint in self.constraints
        ):
            raise TypeError("Design space constraints must be a list of str")

    def size_unconstrained(self) -> int:
        return math.prod(len(values) for values in self.parameters.values())


def convert_design_space_implicit_to_explicit(
    design_space_implicit: DesignSpaceImplicit,
    max_points: int | None = None,
    seed: int = 42,
) -> DesignSpaceExplicit:
    """Expand to every point satisfying the constraints, in product order.

    If max_points is set and exceeded, keep a seeded random sample of that size.
    """
    design_space_implicit.type_check_design_space()
    env = SandboxedEnvironment(undefined=StrictUndefined)
    constraints = [
        env.compile_expression(constraint, undefined_to_none=False)
        for constraint in design_space_implicit.constraints
    ]
    keys = list(design_space_implicit.parameters)
    points: list[T_design_space_point] = []
    for combo in itertools.product(*design_space_implicit.parameters.values()):
        point = dict(zip(keys, combo, strict=True))
        if all(constraint(**point) for constraint in constraints):
            points.append(point)
    if max_points is not None and len(points) > max_points:
        kept = sorted(random.Random(seed).sample(range(len(points)), max_points))
        points = [points[i] for i in kept]
    return DesignSpaceExplicit(points)


def _as_explicit(
    design_space: DesignSpaceExplicit | DesignSpaceImplicit,
) -> DesignSpaceExplicit:
    if isinstance(design_space, DesignSpaceImplicit):
        return convert_design_space_implicit_to_explicit(design_space)
    return design_space


T_sources = dict[str, str]


def _collapse_blank_lines(source: str) -> str:
    return re.sub(r"(?m)^[ \t]*\r?\n(?:[ \t]*\r?\n)+", "\n", source)


class PreprocessorParamaterizationFlow:
    """Preprocess each design-space point with pcpp's command argument API."""

    def preprocess(
        self, sources: T_sources, design_space: DesignSpaceExplicit | DesignSpaceImplicit
    ) -> list[T_sources]:
        design_space = _as_explicit(design_space)
        designs = []

        for point in design_space.design_space:
            new_sources = {}

            defines: list[str] = []
            for key, val in point.items():
                if isinstance(val, bool):
                    if val:
                        defines.extend(["-D", key])
                else:
                    defines.extend(["-D", f"{key}={val}"])

            for src_name, src_content in sources.items():
                with TemporaryDirectory() as tmp_dir:
                    input_file = Path(tmp_dir) / "input.cpp"
                    output_file = Path(tmp_dir) / "output.cpp"
                    input_file.write_text(src_content)
                    fake_argv = [
                        sys.argv[0],
                        "-o",
                        str(output_file),
                        "-I",
                        str(Path(src_name).resolve().parent),
                        "--passthru-includes",
                        ".*",
                        "--passthru-unfound-includes",
                        "--line-directive=",
                    ]
                    fake_argv += defines
                    fake_argv += [str(input_file)]

                    diagnostics = StringIO()
                    with redirect_stdout(diagnostics), redirect_stderr(diagnostics):
                        preprocessor = CmdPreprocessor(fake_argv)
                    if preprocessor.return_code:
                        raise RuntimeError(
                            f"Preprocessing failed for source {src_name} with defines "
                            f"{point}: {diagnostics.getvalue().strip()}"
                        )
                    new_sources[src_name] = _collapse_blank_lines(output_file.read_text())
            designs.append(new_sources)
        return designs


class PreprocessorClangParamaterizationFlow:
    """Expand source macros and conditionals, preserving includes without reading them."""

    # Skip comments and literals so apparent directives inside them stay untouched.
    _include_pattern = re.compile(
        r"//(?:\\\r?\n|[^\r\n])*|/\*[\s\S]*?\*/"
        r'|R"(?P<delimiter>[^ ()\\\t\r\n]{0,16})\([\s\S]*?\)(?P=delimiter)"'
        r'|"(?:\\[\s\S]|[^"\\\r\n])*"'
        r"|'(?:\\[\s\S]|[^'\\\r\n])*'"
        r"|(?P<include>^[ \t]*\#[ \t]*include\b(?:\\\r?\n|[^\r\n])*)",
        re.MULTILINE,
    )

    def __init__(self, bin_clang: Path | str = "clang"):
        self.bin_clang = str(bin_clang)

    def preprocess(
        self, sources: T_sources, design_space: DesignSpaceExplicit | DesignSpaceImplicit
    ) -> list[T_sources]:
        design_space = _as_explicit(design_space)
        designs = []
        for point in design_space.design_space:
            defines: list[str] = []
            for key, val in point.items():
                if isinstance(val, bool):
                    if val:
                        defines.extend(["-D", key])
                else:
                    defines.extend(["-D", f"{key}={val}"])

            new_sources = {}
            for src_name, src_content in sources.items():
                includes = []
                marker = f"hls_eval_include_{uuid4().hex}"

                def shield_include(match):
                    if match.group("include") is None:
                        return match.group()
                    includes.append(match.group())
                    return f"#pragma {marker} {len(includes) - 1}"

                protected_source = self._include_pattern.sub(
                    shield_include, src_content
                )
                cmd = [
                    self.bin_clang,
                    "-E",
                    "-P",
                    "-x",
                    "c++",
                    "-I",
                    str(Path(src_name).resolve().parent),
                    *defines,
                    "-",
                ]
                try:
                    result = subprocess.run(
                        cmd,
                        input=protected_source,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                except subprocess.CalledProcessError as error:
                    raise RuntimeError(
                        f"Preprocessing failed for source {src_name} with defines "
                        f"{point}: {error.stderr.strip()}"
                    ) from error
                preprocessed_source = re.sub(
                    rf"(?m)^#pragma {marker} (\d+)[ \t]*$",
                    lambda match: includes[int(match.group(1))],
                    result.stdout,
                )
                new_sources[src_name] = _collapse_blank_lines(preprocessed_source)
            designs.append(new_sources)
        return designs


class JinjaParamaterizationFlow:
    def __init__(self, *, strict_undefined: bool = False, sandboxed: bool = False):
        self.strict_undefined = strict_undefined
        self.sandboxed = sandboxed

    def preprocess(
        self, sources: T_sources, design_space: DesignSpaceExplicit | DesignSpaceImplicit
    ) -> list[T_sources]:
        design_space = _as_explicit(design_space)
        designs = []

        for point in design_space.design_space:
            new_sources = {}

            for src_name, src_content in sources.items():
                undefined = StrictUndefined if self.strict_undefined else Undefined
                t: Template
                if self.sandboxed:
                    t = SandboxedEnvironment(undefined=undefined).from_string(src_content)
                else:
                    t = Template(src_content, undefined=undefined)
                rendered_content = t.render(**point)
                new_sources[src_name] = _collapse_blank_lines(rendered_content)

            designs.append(new_sources)

        return designs
