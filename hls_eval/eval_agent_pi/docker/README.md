The agent image includes the small runtime dependencies for host-mounted
Vitis HLS (`libtinfo5` and the generated `en_US.UTF-8` locale). Vendor tools
stay on the host and are mounted read-only for each agent run.
The image also installs `uv`, `uvx`, and `pixi` using their official curl
installers into `/usr/local/bin`, available on `PATH` with or without Vitis
configured.

Build the image once, from the repository root:

```bash
bash hls_eval/eval_agent_pi/docker/build_docker_image.sh
```

Pass the installation directory when constructing the evaluator:

```python
evaluator = HLSGenerationAgentEvaluatorPi(
    vitis_hls_tool_csim=csim_tool,
    vitis_hls_tool_synth=synth_tool,
    output_data_dir=output_dir,
    vitis_dir="/opt/Xilinx/Vitis_HLS/2024.1",
)
```

`run_pi_agent(..., vitis_dir=...)` accepts the same setting. Omitting it keeps
the existing behavior without vendor mounts. The experiment in
`hls_eval_experiments/hls_gen_agent_pi/exp.py` passes its discovered HLS
directory to the evaluator. This option configures tools inside the agent
container; the evaluator's host-side C simulation and synthesis tool objects
are still configured separately.

Supported directory layouts:

| Input `vitis_dir` | HLS selected | Vivado inferred |
| --- | --- | --- |
| `<root>/Vitis_HLS/2024.1` | `vitis_hls` | `<root>/Vivado/2024.1` |
| `<root>/Vitis/2024.1` | Sibling `Vitis_HLS/2024.1`, when present | `<root>/Vivado/2024.1` |
| `<root>/Vitis/2024.2` | `vitis-run`, when standalone HLS is absent | `<root>/Vivado/2024.2` |
| `<root>/2025.2/Vitis` or `<root>/2025.2` | `vitis-run` | `<root>/2025.2/Vivado` |

Version numbers above illustrate the layouts. Pass a specific release rather
than an unversioned directory containing multiple releases. Host symlinks
are resolved before mounting. For unified installations the release directory
is mounted, including its shared `data`, `lnx64`, `tps`, `gnu`, and `SharedData`
directories. Mounting just `Vitis/` would break its links to those directories.

For a nonstandard Vivado location, also pass
`vivado_dir="/somewhere/Vivado/2024.1"`. It must match the HLS release.
Missing tools or part data produce an error before the agent container starts.
For a network license server, pass
`vitis_license_server="2100@license.example.org"`; this becomes
`XILINXD_LICENSE_FILE` inside the container. The server must be reachable from
Docker. Local license files are not automatically mounted.

The automation sets `XILINX_HLS`, `XILINX_VIVADO`, and (for integrated HLS)
`XILINX_VITIS` to the container paths. It runs Pi through `with-vitis`, which
adds the component binaries to `PATH` for Pi and its child processes.
This wrapper runs on the actual `docker exec` command, since environment
changes in a container entrypoint would not propagate to later execs.
It does not source vendor setup scripts containing host-specific absolute
paths, and does not put vendor compatibility libraries on Pi's
`LD_LIBRARY_PATH`. The vendor launchers set their own internal library paths;
the image supplies `libtinfo5` directly. No host locale mount is needed.

Validate an installation without an LLM call:

```bash
bash hls_eval/eval_agent_pi/docker/test_vitis_mount.sh \
    --vitis-dir /tools/software/xilinx/ARCHIVE/Vitis_HLS/2024.1

# Unified installation:
bash hls_eval/eval_agent_pi/docker/test_vitis_mount.sh \
    --vitis-dir /tools/software/amd/xilinx/2025.2.1/Vitis
```

The smoke test uses the same resolver and launcher as the evaluator. It runs
C simulation and synthesis of an `ap_int` dot product targeting
`xc7z020clg400-1`, checks both logs and generated RTL/reports, and prints the
retained results directory under `/tmp`. It runs as your UID/GID and removes
the container afterward. Options include `--vivado-dir`, `--license-server`,
and `--image`. The shell wrapper uses the project's `uv` environment.

This setup targets batch HLS workflows. GUI use, RTL co-simulation, and Vivado
implementation require separate validation. Other releases may need additional
OS dependencies; the smoke test checks the installation supplied by the caller.

Validated on 2026-09-11 with rebuilt image `401d2f13aefd`: C simulation and
synthesis passed for the server's Vitis HLS 2024.1 directory (reports 2024.1.2)
and unified Vitis 2025.2.1 installation. Pi also started successfully with
each tool environment and with no vendor mounts or configuration. No host
locale mount, custom `LD_LIBRARY_PATH`, or license environment was needed
for these smoke tests.
