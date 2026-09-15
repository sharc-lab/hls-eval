"""Exercise the same mount configuration and launcher used by run_pi_agent."""

import argparse
import os
import shutil
import tempfile
from contextlib import closing
from pathlib import Path

import docker

from hls_eval.eval_agent_pi.vitis import VitisInstallation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vitis-dir", type=Path, required=True)
    parser.add_argument("--vivado-dir", type=Path)
    parser.add_argument("--license-server")
    parser.add_argument("--image", default="hls-eval-agent-pi")
    args = parser.parse_args()
    installation = VitisInstallation.from_path(
        args.vitis_dir, args.vivado_dir, args.license_server
    )
    work_dir = Path(tempfile.mkdtemp(prefix="hls-eval-vitis-mount."))
    for source in (Path(__file__).parent / "vitis_smoke").iterdir():
        shutil.copyfile(source, work_dir / source.name)
    print(f"Image: {args.image}\nResults: {work_dir}", flush=True)

    # Use exec_run, as the evaluator does, to verify PATH initialization is
    # applied to the agent's process and not just to container startup.
    with closing(docker.from_env()) as client:
        container = client.containers.run(
            args.image,
            command="sleep 10m",
            detach=True,
            user=f"{os.getuid()}:{os.getgid()}",
            volumes={
                **installation.volumes,
                str(work_dir): {"bind": "/workspace", "mode": "rw"},
            },
            environment={**installation.environment, "HOME": "/workspace"},
            working_dir="/workspace",
        )
        try:
            pi_check = container.exec_run(["with-vitis", "pi", "--version"])
            if pi_check.exit_code != 0:
                raise RuntimeError(pi_check.output.decode("utf-8", errors="replace"))
            result = container.exec_run(
                [
                    "with-vitis",
                    "timeout",
                    "300",
                    *installation.hls_command,
                    "smoke.tcl",
                ],
                workdir="/workspace",
            )
        finally:
            container.remove(force=True)

    output = result.output.decode("utf-8", errors="replace")
    (work_dir / "run.log").write_text(output)
    print(output)
    # Some HLS initialization failures incorrectly return exit code zero.
    solution = work_dir / "smoke_project/solution1"
    if (
        result.exit_code != 0
        or "CSim done with 0 errors" not in output
        or "Finished Command csynth_design" not in output
        or not (solution / "syn/report/dot4_csynth.xml").is_file()
        or not (solution / "syn/verilog/dot4.v").is_file()
    ):
        raise SystemExit(f"FAIL: see {work_dir / 'run.log'}")
    print(f"PASS: C simulation and RTL synthesis completed. Results: {work_dir}")


if __name__ == "__main__":
    main()
