import shutil
from pathlib import Path

import tomllib

CPP_EXTENSIONS = [
    ".c",
    ".cc",
    ".cpp",
]
H_EXTENSIONS = [
    ".h",
    ".hh",
    ".hpp",
]
SOURCE_FILE_EXTENSIONS = CPP_EXTENSIONS + H_EXTENSIONS


# @dataclass
# class BenchmarkCase:
#     design_dir: Path
#     tags: list[str] = field(default_factory=list)


class BenchmarkCase:
    def __init__(
        self, design_dir: Path, name: str | None = None, tags_user: list[str] = []
    ):
        self.design_dir = design_dir
        if name is None:
            name = design_dir.name
        self.name = name
        self.tags_user = tags_user

        # check that the dir exists
        if not self.design_dir.exists():
            raise FileNotFoundError(
                f"Design directory {self.design_dir} does not exist"
            )

        if not self.design_dir.is_dir():
            raise NotADirectoryError(
                f"Design directory {self.design_dir} is not a directory"
            )

        # check if it containts a non empty top.txt file
        if not self.top_file.exists():
            raise FileNotFoundError(f"Top file {self.top_file} does not exist")
        if self.top_file.is_dir():
            raise IsADirectoryError(f"Top file {self.top_file} is a directory")
        if not self.top_file.read_text().strip():
            raise ValueError(f"Top file {self.top_file} is empty")

        # check if a single _tb file exists
        tb_matches = [f for f in self.files if f.stem.endswith("_tb")]
        if len(tb_matches) != 1:
            raise ValueError(f"Expected 1 _tb file, found {len(tb_matches)}")
        tb_file = tb_matches[0]
        if not tb_file.exists():
            raise FileNotFoundError(f"Testbench file {tb_file} does not exist")
        if tb_file.is_dir():
            raise IsADirectoryError(f"Testbench file {tb_file} is a directory")
        if not tb_file.read_text().strip():
            raise ValueError(f"Testbench file {tb_file} is empty")

        # check if a kernel_description.md file exists
        kernel_description_fp = self.design_dir / "kernel_description.md"
        if not kernel_description_fp.exists():
            raise FileNotFoundError(
                f"Kernel description file {kernel_description_fp} does not exist"
            )
        if kernel_description_fp.is_dir():
            raise IsADirectoryError(
                f"Kernel description file {kernel_description_fp} is a directory"
            )
        if not kernel_description_fp.read_text().strip():
            raise ValueError(
                f"Kernel description file {kernel_description_fp} is empty"
            )

        # check hls_eval_config.toml exists
        if not (self.design_dir / "hls_eval_config.toml").exists():
            raise FileNotFoundError(
                f"hls_eval_config.toml file does not exist in {self.design_dir}"
            )
        if (self.design_dir / "hls_eval_config.toml").is_dir():
            raise IsADirectoryError(
                f"hls_eval_config.toml file is a directory in {self.design_dir}"
            )
        if not (self.design_dir / "hls_eval_config.toml").read_text().strip():
            raise ValueError(f"hls_eval_config.toml file is empty in {self.design_dir}")

    @property
    def files(self) -> list[Path]:
        return [f for f in self.design_dir.rglob("*") if f.is_file()]

    @property
    def source_files(self) -> list[Path]:
        return [f for f in self.files if f.suffix in SOURCE_FILE_EXTENSIONS]

    @property
    def h_files(self) -> list[Path]:
        return [f for f in self.files if f.suffix in H_EXTENSIONS]

    @property
    def cpp_files(self) -> list[Path]:
        return [f for f in self.files if f.suffix in CPP_EXTENSIONS]

    @property
    def not_source_files(self) -> list[Path]:
        return [f for f in self.files if f.suffix not in SOURCE_FILE_EXTENSIONS]

    @property
    def tb_file(self) -> Path:
        tb_matches = [f for f in self.files if f.name.endswith("_tb.cpp")]
        if len(tb_matches) != 1:
            raise ValueError(f"Expected 1 _tb file, found {len(tb_matches)}")
        return tb_matches[0]

    @property
    def kernel_description_fp(self) -> Path:
        fp = self.design_dir / "kernel_description.md"
        if not fp.exists():
            raise FileNotFoundError(f"Kernel description file {fp} does not exist")
        return fp

    @property
    def top_file(self) -> Path:
        return self.design_dir / "top.txt"

    @property
    def top_fn(self) -> str:
        top_fn = self.top_file.read_text().strip()
        if not top_fn:
            raise ValueError(f"Top file {self.top_file} is empty")
        return top_fn

    @property
    def toml_data(self) -> dict:
        return tomllib.loads((self.design_dir / "hls_eval_config.toml").read_text())

    @property
    def tags_all(self) -> list[str]:
        return self.toml_data.get("tags", []) + self.tags_user

    @property
    def tags_in_config(self) -> list[str]:
        return self.toml_data.get("tags", [])

    def copy_to(self, dest: Path) -> "BenchmarkCase":
        shutil.copytree(
            self.design_dir,
            dst=dest,
        )
        return BenchmarkCase(dest, tags_user=self.tags_user)


def find_benchmark_case_dirs(start_dir) -> list[Path]:
    all_dirs = [d for d in start_dir.rglob("*") if d.is_dir()]
    benchmark_case_dirs = [d for d in all_dirs if (d / "hls_eval_config.toml").exists()]
    return benchmark_case_dirs
