"""Exercise the dataflow agent image in both access modes, without an LLM.

Containers are configured exactly as the evaluator does it
(`_agent_container_options`): with the tools, LightningSim and FIFOAdvisor must
run on a design the agent synthesizes itself, using the same Tcl recipe the
prompt gives it; without them, the tools must not exist or be installable.
"""

import argparse
import shutil
import tempfile
from contextlib import closing
from pathlib import Path

import docker

from hls_eval.eval_agent_pi.eval_agent_pi_paramaterized_dataflow import (
    BLOCKED_HOSTS,
    HARNESS_SYNTH_CONFIG_TCL,
    DATAFLOW_DOCKER_IMAGE_NAME,
    DATAFLOW_TOOLS_CONTAINER_DIR,
)
from hls_eval.eval_agent_pi.vitis import VitisInstallation

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DESIGN = ROOT / "hls_eval_data_accel" / "stream_hls" / "atax"

RECIPE = """open_project -reset proj
add_files {kernel}
add_files -tb {tb}
{tb_data}
set_top {top}
open_solution solution1 -flow_target vivado
set_part xczu9eg-ffvb1156-2-e
create_clock -period 5 -name clk_default
{config}
csynth_design
exit
"""


def sh(container, command: str, wrappers: tuple[str, ...] = ()) -> tuple[int, str]:
    result = container.exec_run([*wrappers, "sh", "-lc", command], workdir="/workspace")
    return result.exit_code, result.output.decode("utf-8", errors="replace")


def check(condition: bool, message: str, output: str = "") -> None:
    print(("PASS: " if condition else "FAIL: ") + message, flush=True)
    if not condition:
        raise SystemExit(f"FAIL: {message}\n{output}")


def run_tools_mode(client, args, installation, design: Path, work_dir: Path) -> None:
    kernel = next(
        p.name for p in design.glob("*.cpp") if not p.name.endswith("_tb.cpp")
    )
    tb = next(p.name for p in design.glob("*_tb.cpp"))
    data = [p.name for p in design.glob("*.bin")]
    (work_dir / "run.tcl").write_text(
        RECIPE.format(
            kernel=kernel,
            tb=tb,
            tb_data="\n".join(f"add_files -tb {name}" for name in data),
            top=(design / "top.txt").read_text().strip(),
            config="\n".join(HARNESS_SYNTH_CONFIG_TCL),
        )
    )
    container = client.containers.run(
        args.image,
        command="sleep 30m",
        detach=True,
        volumes={
            **installation.volumes,
            str(work_dir): {"bind": "/workspace", "mode": "rw"},
        },
        environment=installation.environment,
        working_dir="/workspace",
    )
    wrappers = ("with-vitis", "with-dataflow-tools")
    try:
        code, out = sh(
            container, "command -v lightningsim fifo-advisor hls-python", wrappers
        )
        check(code == 0, "tools are on PATH with the wrapper", out)
        code, out = sh(
            container, "hls-python -c 'import lightningsim, fifo_advisor'", wrappers
        )
        check(code == 0, "lightningsim and fifo_advisor import", out)
        code, out = sh(container, "timeout 600 vitis_hls -f run.tcl", wrappers)
        check(
            code == 0 and (work_dir / "proj/solution1/syn/report").is_dir(),
            "the prompt's Tcl recipe synthesizes the design with its testbench",
            out[-3000:],
        )
        code, out = sh(container, "timeout 900 lightningsim proj/solution1", wrappers)
        check(
            code == 0 and "Simulation finished" in out,
            "LightningSim simulates the synthesized design in the container",
            out[-3000:],
        )
        print(out.strip().splitlines()[-6:], flush=True)
        code, out = sh(
            container,
            "timeout 900 fifo-advisor proj/solution1 --solver heuristic --output r.json",
            wrappers,
        )
        check(
            code == 0 and (work_dir / "r.json").is_file(),
            "FIFOAdvisor runs in the container",
            out[-3000:],
        )
        sh(container, "chmod -R a+rwX /workspace")  # container runs as root
    finally:
        container.remove(force=True)


def run_disabled_mode(client, args, work_dir: Path) -> None:
    # Exactly the evaluator's tools-off configuration: no Vitis mount, environment
    # or `with-vitis` wrapper, and the tools masked and their hosts blocked.
    container = client.containers.run(
        args.image,
        command="sleep 10m",
        detach=True,
        volumes={str(work_dir): {"bind": "/workspace", "mode": "rw"}},
        working_dir="/workspace",
        tmpfs={DATAFLOW_TOOLS_CONTAINER_DIR: "size=1m,mode=0755"},
        extra_hosts={host: "127.0.0.1" for host in BLOCKED_HOSTS},
    )
    try:
        code, out = sh(
            container, "command -v lightningsim fifo-advisor hls-python vitis_hls"
        )
        check(code != 0 and not out.strip(), "no tool and no vitis_hls on PATH", out)
        code, out = sh(
            container,
            "! env | grep -qi 'xilinx\\|vitis\\|vivado' && test ! -e /opt/amd",
        )
        check(code == 0, "no Vitis environment variables or mount", out)
        code, out = sh(container, f"ls -A {DATAFLOW_TOOLS_CONTAINER_DIR}")
        check(code == 0 and not out.strip(), "the tool directory is empty", out)
        code, out = sh(container, "with-dataflow-tools true")
        check(code != 0, "the tools wrapper refuses to run", out)
        # getaddrinfo is what curl, pip and pixi use; plain `getent hosts` takes a
        # different, IPv6-first path and would show DNS answers.
        code, out = sh(container, "getent ahosts sharc-lab.github.io github.com")
        check(
            code == 0
            and {line.split()[0] for line in out.splitlines()} == {"127.0.0.1"},
            "the tools' download hosts resolve to loopback",
            out,
        )
        code, out = sh(
            container,
            "curl -sS -m 10 -o /dev/null https://sharc-lab.github.io/LightningSim/repo/linux-64/repodata.json",
        )
        check(code != 0, "the LightningSim conda channel is unreachable", out)
        code, out = sh(
            container,
            "curl -sS -m 10 -o /dev/null https://github.com/sharc-lab/fifo-advisor",
        )
        check(code != 0, "the FIFOAdvisor repository is unreachable", out)
        code, out = sh(
            container, "curl -sS -m 20 -o /dev/null https://pypi.org/simple/jinja2/"
        )
        check(code == 0, "unrelated hosts (PyPI) stay reachable", out)
        code, out = sh(
            container,
            "python3 -c 'import sys; print(sys.prefix)'; find / -xdev \\( -name 'lightningsim*' -o -name 'fifo_advisor*' \\) -not -path '/proc/*' 2>/dev/null | head",
        )
        check(
            not out.split("\n", 1)[1].strip(),
            "no LightningSim/FIFOAdvisor files exist anywhere",
            out,
        )
    finally:
        container.remove(force=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vitis-dir", type=Path, required=True)
    parser.add_argument("--vivado-dir", type=Path)
    parser.add_argument("--license-server")
    parser.add_argument("--image", default=DATAFLOW_DOCKER_IMAGE_NAME)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
    args = parser.parse_args()
    installation = VitisInstallation.from_path(
        args.vitis_dir, args.vivado_dir, args.license_server
    )
    work_dir = Path(tempfile.mkdtemp(prefix="hls-eval-dataflow-image."))
    for source in args.design.iterdir():
        if source.is_file():
            shutil.copyfile(source, work_dir / source.name)
    print(f"Image: {args.image}\nResults: {work_dir}", flush=True)
    with closing(docker.from_env()) as client:
        run_disabled_mode(client, args, work_dir)
        run_tools_mode(client, args, installation, args.design, work_dir)
    print(f"PASS: both access modes behave as configured. Results: {work_dir}")


if __name__ == "__main__":
    main()
