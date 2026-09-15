import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from hls_eval.eval_agent_pi.eval_agent_pi import run_pi_agent
from hls_eval.eval_agent_pi.vitis import VitisInstallation


def touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def make_vivado(path):
    touch(path / "bin/vivado")
    (path / "data/parts").mkdir(parents=True)
    return path


@pytest.fixture
def legacy(tmp_path):
    hls = tmp_path / "AMD tools/Vitis_HLS/2024.1"
    touch(hls / "bin/vitis_hls")
    make_vivado(tmp_path / "AMD tools/Vivado/2024.1")
    return hls


def test_legacy_symlink_and_vitis_path_find_matching_components(legacy, tmp_path):
    alias = tmp_path / "alias"
    alias.symlink_to(legacy, target_is_directory=True)
    vitis = legacy.parent.parent / "Vitis/2024.1"
    touch(vitis / "bin/vitis-run")
    for source in (legacy, alias, vitis):
        config = VitisInstallation.from_path(source)
        assert str(legacy) in config.volumes
        assert str(legacy.parent.parent / "Vivado/2024.1") in config.volumes
        assert all(mount["mode"] == "ro" for mount in config.volumes.values())
        assert config.hls_command == ("vitis_hls", "-f")


@pytest.mark.parametrize("release_root", [False, True])
def test_unified_mount_preserves_shared_directories(tmp_path, release_root):
    release = tmp_path / "2025.2"
    vitis = release / "Vitis"
    touch(vitis / "bin/vitis-run")
    make_vivado(release / "Vivado")
    (release / "lnx64").mkdir()
    (vitis / "lnx64").symlink_to("../lnx64", target_is_directory=True)
    config = VitisInstallation.from_path(release if release_root else vitis)
    assert config.volumes == {str(release): {"bind": "/opt/amd/release", "mode": "ro"}}
    assert config.environment["XILINX_HLS"] == "/opt/amd/release/Vitis"
    assert config.environment["XILINX_VIVADO"] == "/opt/amd/release/Vivado"
    assert config.hls_command == ("vitis-run", "--mode", "hls", "--tcl")


def test_integrated_hls_in_older_directory_layout(tmp_path):
    tool = tmp_path / "Vitis/2024.2"
    touch(tool / "bin/vitis-run")
    make_vivado(tmp_path / "Vivado/2024.2")
    config = VitisInstallation.from_path(tool)
    assert str(tool) in config.volumes
    assert config.environment["XILINX_VITIS"] == config.environment["XILINX_HLS"]


def test_custom_vivado_location_and_license(legacy, tmp_path):
    vivado = make_vivado(tmp_path / "separate-vivado")
    config = VitisInstallation.from_path(legacy, vivado, "2100@license.example")
    assert str(vivado) in config.volumes
    assert config.environment["XILINXD_LICENSE_FILE"] == "2100@license.example"


def test_missing_matching_vivado_fails_with_override_hint(tmp_path):
    tool = tmp_path / "Vitis_HLS/2024.1"
    touch(tool / "bin/vitis_hls")
    make_vivado(tmp_path / "Vivado/2023.1")
    with pytest.raises(ValueError, match="Pass vivado_dir"):
        VitisInstallation.from_path(tool)


def test_unversioned_install_root_is_not_guessed(legacy):
    with pytest.raises(ValueError, match="versioned"):
        VitisInstallation.from_path(legacy.parent.parent)


def test_launcher_exposes_tools_to_child_process_without_settings(tmp_path):
    root = tmp_path / "relocated tool"
    executable = root / "bin/vitis_hls"
    executable.parent.mkdir(parents=True)
    executable.write_text('#!/bin/sh\nprintf "mounted-tool"\n')
    executable.chmod(0o755)
    launcher = Path(__file__).parents[1] / "hls_eval/eval_agent_pi/docker/with-vitis"
    result = subprocess.run(
        ["bash", str(launcher), "sh", "-c", "vitis_hls"],
        env={"PATH": "/usr/bin:/bin", "XILINX_HLS": str(root)},
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "mounted-tool"


@pytest.mark.parametrize("mount_vitis", [False, True])
def test_agent_mounts_tools_and_wraps_actual_exec(
    legacy, tmp_path, monkeypatch, mount_vitis
):
    container = Mock()
    container.exec_run.return_value = (0, b"agent finished")
    client = Mock()
    client.containers.run.return_value = container
    monkeypatch.setattr(
        "hls_eval.eval_agent_pi.eval_agent_pi.docker.from_env", lambda: client
    )
    run_dir = tmp_path / "run"
    result = run_pi_agent(
        run_dir,
        "prompt with ' quotes and $(shell)",
        "test-model",
        "test-key",
        vitis_dir=legacy if mount_vitis else None,
    )
    options = client.containers.run.call_args.kwargs
    assert options["volumes"][str(run_dir)]["mode"] == "rw"
    command = container.exec_run.call_args.args[0][-1]
    if mount_vitis:
        assert options["volumes"][str(legacy)]["mode"] == "ro"
        assert options["environment"]["XILINX_HLS"] == "/opt/amd/hls"
        assert "with-vitis pi -p" in command
    else:
        assert len(options["volumes"]) == 1
        assert "with-vitis" not in command
    assert "test-key" not in options["environment"].values()
    assert result.exit_code == 0
    container.stop.assert_called_once()
    container.remove.assert_called_once_with(force=True)
