from pathlib import Path
from textwrap import dedent

from hls_eval.prompting import build_input_code_prompt_xml

prompt_synth_prep = dedent("""
## Task Description
Your task is to edit the given user's HLS code to prepare it for synthesis using Vitis HLS.
The code should be modified to ensure that it is synthesizable by the Vitis HLS tool.
                           
All C-style arrays need and array function arguments need to be declared and passed as fixed sized arrays.
For example `int* arr` should be converted to `int arr[SIZE]` and any functions that take `int* arr` as an argument should be changed to take `int arr[SIZE]` as an argument.
This also needs to be adapted for multi-dimensional arrays.
If any array dimension size parameters are needed for the fixed-size arrays, they should be defined as constants at the top of the file.
All arrays needed to have explicit sizes. For example, `int arr[]` should not be used; instead, use `int arr[SIZE]`.

There should be no recursion in the code; if so, refactor the code to remove recursion.
There should be no printf or sprintf statements in the code; if so, comment them out.
There should be no dynamic memory allocation in the code; if so, refactor the code to remove dynamic memory allocation and use fixed-size arrays.
There should be no usage of pointers, pointer dereferencing, or pointer arithmetic in the code; if so, refactor the code to remove pointers.

Floating-point data types and operations should be converted to fixed-point data types and operations when appropriate.
Please only do this conversion for `float` and double `types`.

All loops should have loop labels added to them using the `label: statement` syntax.
                           
Inserting Vitis HLS pragmas as needed (i.e. using `#pragma HLS ...`).

Please complete all the above steps to prepare the code for synthesis.
Do not over-optimize the code; the goal is to make the code synthesizable and slightly optimized as a starting point for further optimization.

You do not need to include any testbench code modifications in the output; these file (`*_tb.cpp`) should not be listed in the output.
""").strip()


prompt_pre = dedent(
    """
## Overview
You are a helpful export hardware engineer and software developer who will assist the user with hardware design tasks for high-level synthesis.
The task will center around high-level synthesis (HLS) code written in C++ for a hardware design. The HLS design is written to target the latest Vitis HLS tool from Xilinx, which maps C++ code to a Verilog implementation for FPGAs.
"""
).strip()

prompt_gen = dedent(
    """
## Task Description"
Given a natural language description of an HLS design, a pre-written C++ design header, and a pre-written C++ testbench, generate the C++ implementation of the HLS design that aligns with the natural language description.

It should be functionally equivalent to the natural language description, be consistent with the provided header file, and pass the testbench. The design should also be synthesizable by the HLS tool.

Only generate the code for the design; do not modify the header file or the testbench. Make sure to import the header file as well.

Provide the complete design code in the single output; do not omit anything or leave placeholders.

Hierarchical design, sub-functions, template functions, structs, typedefs, and define statements are allowed but should be used only if appropriate.
"""
).strip()


prompt_output_format_xml = dedent(
    text="""
## Output Format
The generated HLS output code should be provided in the following format:
```
<OUTPUT_CODE name="kernel_name.cpp">
    ...
</OUTPUT_CODE>
```
Please use this XML format and do not use other formats like markdown code blocks or plain text.
Only output the generated HLS code in the XML format and nothing else.
"""
).strip()


def build_prompt_gen_zero_shot(
    design_description_fp: Path, design_tb: Path, design_h: Path
) -> str:
    p = prompt_pre
    p += "\n\n"
    p += prompt_gen
    p += "\n\n"
    p += prompt_output_format_xml
    p += "\n\n"

    p += "## Task Inputs\n"
    p += "\n"
    code = build_input_code_prompt_xml(
        {
            design_description_fp.name: design_description_fp.read_text(),
            design_tb.name: design_tb.read_text(),
            design_h.name: design_h.read_text(),
        }
    )
    p += code
    p += "\n\n"

    p += "## Task Output\n"
    p += "\n"

    return p
