import shutil
from dataclasses import dataclass, field
from pathlib import Path

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


@dataclass
class BenchmarkCase:
    design_dir: str
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        # check that the dir exists
        if not self.design_dir.exists():
            raise FileNotFoundError(
                f"Design directory {self.design_dir} does not exist"
            )

        if not self.design_dir.is_dir():
            raise NotADirectoryError(
                f"Design directory {self.design_dir} is not a directory"
            )

    @property
    def name(self) -> str:
        return self.design_dir.name

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
    def top_file(self) -> Path:
        return self.design_dir / "top.txt"

    @property
    def top_fn(self) -> str:
        top_fn = self.top_file.read_text().strip()
        if not top_fn:
            raise ValueError(f"Top file {self.top_file} is empty")
        return top_fn

    # @property
    # def makefile(self) -> Path:
    #     return find_file(self, ["makefile", "Makefile"])

    # @property
    # def readme(self) -> Path:
    #     return find_file(self, ["readme", "README", "readme.md", "README.md"])

    def copy_to(self, dest: Path) -> "BenchmarkCase":
        current_dir_name = self.design_dir.name
        if not dest.exists():
            raise FileNotFoundError(f"Design directory {dest} does not exist")
        dest = dest / current_dir_name
        shutil.copytree(self.design_dir, dest)
        return BenchmarkCase(dest, tags=self.tags)
