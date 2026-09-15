"""Resolve host installations into read-only Docker mounts for the Pi agent."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VitisInstallation:
    volumes: dict[str, dict[str, str]]
    environment: dict[str, str]
    hls_command: tuple[str, ...]

    @classmethod
    def from_path(
        cls,
        vitis_dir: str | Path,
        vivado_dir: str | Path | None = None,
        license_server: str | None = None,
    ) -> "VitisInstallation":
        """Accept a versioned Vitis/Vitis_HLS directory or a unified release root.

        Legacy: <root>/Vitis_HLS/<version>, <root>/Vitis/<version>.
        Unified: <root>/<version>/Vitis, or <root>/<version>.
        An unversioned root with multiple releases is intentionally not guessed.
        """
        tool = Path(vitis_dir).expanduser().resolve(strict=True)
        if (tool / "Vitis/bin/vitis-run").is_file():
            tool = tool / "Vitis"

        # Prefer standalone HLS when given a legacy Vitis installation.
        sibling_hls = tool.parent.parent / "Vitis_HLS" / tool.name
        if tool.parent.name == "Vitis" and (sibling_hls / "bin/vitis_hls").is_file():
            tool = sibling_hls.resolve()

        legacy = (tool / "bin/vitis_hls").is_file()
        integrated = (tool / "bin/vitis-run").is_file()
        unified = integrated and tool.name == "Vitis"
        if not legacy and not integrated:
            raise ValueError(
                f"No supported HLS installation at {tool}. Pass a versioned "
                "Vitis_HLS directory, a Vitis directory, or a unified release "
                "directory containing Vitis/bin/vitis-run."
            )

        volumes: dict[str, dict[str, str]] = {}

        def mount(host: Path, container: str) -> None:
            volumes[str(host)] = {"bind": container, "mode": "ro"}

        hls_command = (
            ("vitis_hls", "-f") if legacy else ("vitis-run", "--mode", "hls", "--tcl")
        )
        if not unified:
            hls_container = "/opt/amd/hls"
            mount(tool, hls_container)
            inferred_vivado = tool.parent.parent / "Vivado" / tool.name
        else:
            # Preserve ../data, ../lnx64, ../tps, ../gnu and SharedData links.
            mount(tool.parent, "/opt/amd/release")
            hls_container = "/opt/amd/release/Vitis"
            inferred_vivado = tool.parent / "Vivado"

        vivado = (
            Path(vivado_dir).expanduser().resolve(strict=True)
            if vivado_dir is not None
            else inferred_vivado.resolve()
        )
        if (
            not (vivado / "bin/vivado").is_file()
            or not (vivado / "data/parts").is_dir()
        ):
            raise ValueError(
                f"Matching Vivado installation not found at {vivado}. "
                "Pass vivado_dir pointing to the matching release (bin/vivado "
                "and data/parts are required)."
            )

        if unified and vivado == inferred_vivado.resolve():
            vivado_container = "/opt/amd/release/Vivado"
        elif vivado.name == "Vivado" and (vivado / "data").is_symlink():
            mount(vivado.parent, "/opt/amd/vivado-release")
            vivado_container = "/opt/amd/vivado-release/Vivado"
        else:
            vivado_container = "/opt/amd/vivado"
            mount(vivado, vivado_container)

        environment = {
            "XILINX_HLS": hls_container,
            "XILINX_VIVADO": vivado_container,
        }
        if not legacy:
            environment["XILINX_VITIS"] = hls_container
        if license_server is not None:
            environment["XILINXD_LICENSE_FILE"] = license_server
        return cls(volumes, environment, hls_command)
