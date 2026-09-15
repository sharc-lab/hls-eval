import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Template

# class DesignSpaceImplicit:


T_design_space_key = str
T_design_space_value = str | int | float | bool
T_design_space_point = dict[T_design_space_key, T_design_space_value]


class DesignSpaceExplicit:
    def __init__(self):
        self.design_space: list[T_design_space_point] = []

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


def convert_design_space_implicit_to_explicit(
    design_space_implicit: DesignSpaceImplicit,
) -> DesignSpaceExplicit:
    raise NotImplementedError


T_sources = dict[str, str]


class PreprocessorParamaterizationFlow:
    def __init__(self, bin_cpp: Path | str):
        self.bin_cpp = Path(bin_cpp)

    def preprocess(
        self, sources: T_sources, design_space: DesignSpaceExplicit
    ) -> list[T_sources]:
        designs = []

        for point in design_space.design_space:
            new_sources = {}

            defines_args: list[str] = []
            for key, val in point.items():
                if isinstance(val, bool):
                    if val:
                        defines_args.append(f"-D{key}")
                else:
                    defines_args.append(f"-D{key}={val}")

            for src_name, src_content in sources.items():
                with (
                    tempfile.NamedTemporaryFile(delete=False) as tmp_input_file,
                    tempfile.NamedTemporaryFile(delete=False) as tmp_output_file,
                ):
                    fp_input = Path(tmp_input_file.name)
                    fp_output = Path(tmp_output_file.name)

                    tmp_input_file.write(src_content.encode())

                    cmd = [
                        "g++",
                        "-E",  # preprocess only
                        "-P",  # inhibit linemarkers (optional)
                        "-x",
                        "c++",
                        str(fp_input.resolve()),
                        "-o",
                        str(fp_output.resolve()),
                    ]
                    cmd[1:1] = defines_args

                    try:
                        subprocess.run(
                            cmd,
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        preprocessed_content = fp_output.read_text()
                        new_sources[src_name] = preprocessed_content
                    except subprocess.CalledProcessError:
                        fp_input.unlink(missing_ok=True)
                        fp_output.unlink(missing_ok=True)
                        raise RuntimeError(
                            f"Preprocessing failed for source {src_name} with defines {defines_args}"
                        )
            designs.append(new_sources)
        return designs


class JinjaParamaterizationFlow:
    def preprocess(
        self, sources: T_sources, design_space: DesignSpaceExplicit
    ) -> list[T_sources]:
        designs = []

        for point in design_space.design_space:
            new_sources = {}

            for src_name, src_content in sources.items():
                t: Template = Template(src_content)
                rendered_content = t.render(**point)
                new_sources[src_name] = rendered_content

            designs.append(new_sources)

        return designs
