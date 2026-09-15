"""Vitis HLS backend — the pre-existing ForgeBench emission behavior.

This backend is deliberately a faithful transcription of what the generators
emitted before the refactor, quirks included, because the committed
`analysis/results_*` metrics were produced from that exact output. Regenerating
any design with `tool: "vitis"` must be byte-identical to the pre-refactor result.

Two quirks are preserved on purpose:
  * `#pragma HLS unroll factor=1` is emitted even when the factor is 1 (the
    partition pragmas, by contrast, are skipped when the factor is 1).
  * `<hls_math.h>` is included twice in top.cpp.
"""
import re

from backends.base import ToolBackend, normalize_data_type, register


def replace_data_type(data_type):
    """Sanitize a C++ type into a legal function-name suffix.

    Original implementation from `gemm/generate_code.py:4`; `ap_fixed<16, 5>`
    becomes `ap_fixed_16_5_`.
    """
    result = re.sub(r"[<>,]", "_", data_type)
    return result.replace(" ", "")


@register
class VitisBackend(ToolBackend):
    name = "vitis"

    # -- types -------------------------------------------------------------

    def type_decl(self, data_type):
        # Legacy configs already spell the Vitis type; pass them through
        # untouched so spacing (`ap_fixed<16, 5>`) survives verbatim.
        if data_type.strip().startswith("ap_"):
            return data_type
        kind, a, b = normalize_data_type(data_type)
        return f"ap_fixed<{a}, {b}>" if kind == "fixed" else a

    def type_suffix(self, data_type):
        return replace_data_type(self.type_decl(data_type))

    # -- includes ----------------------------------------------------------

    def includes_top_cpp(self):
        return [
            "#include <stdio.h>",
            "#include <iostream>",
            "#include <fstream>",
            "#include <cstdlib>",
            "#include <ap_fixed.h>",
            "#include <hls_math.h>",
            "#include <stdlib.h>",
            "#include <cstdint>",
            "#include <hls_math.h>",
        ]

    def includes_top_h(self):
        return ["#include <ap_fixed.h>"]

    def includes_tb(self):
        return [
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <math.h>",
            "#include <ap_fixed.h>",
            '#include "top.h"  // Include the top function declaration',
        ]

    # -- pragmas -----------------------------------------------------------

    def open_loop(self, header, factor):
        # Vitis places the unroll pragma INSIDE the loop body.
        return f"{header} {{\n#pragma HLS unroll factor={factor}\n"

    def array_partition(self, var, factor, dim):
        if int(factor) <= 1:
            return ""
        return (
            f"#pragma HLS array_partition variable={var} "
            f"cyclic factor={factor} dim={dim}\n"
        )

    def interface(self, drams):
        return [
            f"    #pragma HLS interface m_axi port={d['name']} "
            f"offset=slave bundle={d['bundle']}"
            for d in drams
        ]

    # -- build script ------------------------------------------------------

    def emit_script(self, drams, target, clock_period, tasks, output_filename):
        lines = []
        lines.append("# Auto-generated TCL file for HLS")
        lines.append("open_project -reset project_1")
        lines.append("")
        lines.append("set_top top")
        lines.append("")
        lines.append("add_files  top.cpp")
        lines.append("add_files -tb tb_top.cpp")
        lines.append("add_files -tb top.h")
        lines.append("")

        for dram in drams:
            lines.append(f"add_files -tb {dram['name']}.txt")

        lines.append('open_solution "solution1"')
        lines.append("")
        lines.append(f"set_part {target}")
        lines.append("")
        lines.append(f"create_clock -period {clock_period} -name default")
        lines.append("")

        for step, cmd in (
            ("csim", "csim_design"),
            ("csynth", "csynth_design"),
            ("cosim", "cosim_design"),
            ("export_ip", "export_design -format ip_catalog -flow impl"),
        ):
            if step in tasks:
                lines.append(cmd)
                lines.append("")

        lines.append("exit")

        with open(output_filename, "w") as f:
            f.write("\n".join(lines))

    def run_cmd(self):
        return ["vitis_hls", "-f", "run_hls.tcl"]
