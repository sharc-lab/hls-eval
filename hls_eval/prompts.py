from pathlib import Path
from string import Template
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
## Task Description
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


prompt_edit = dedent(
    """
## Task Description
Given a complete implementation of an HLS kernel in C++, a pre-written C++ design header, a pre-written C++ testbench, and a natural language description of the HLS design, generate the edited C++ code of the kernel (and possibly header and testbench) to perform the specific editing task outlined below.

When editing the provided HLS code, do not make new versions of the HLS kernels; edit the provided HLS kernels directly.
Edits should maintain consistency across the kernel, header, and testbench files. For example, changing function signatures and types in the kernel should be reflected in all places relevant in the code.

Make sure the resulting edited code is still correct syntactically and functionally so that it will pass compilation, testbench execution, and HLS synthesis.
"""
).strip()


prompt_loop_labels = dedent("""
### Editing Task - Loop Labels
Your task is to modify the given user's code to insert loop labels into the user's kernel (including in the kernel's top function, and any kernel subfunctions).
Only insert the loop labels; don't modify the actual loop code or insert any other pragmas.
Use the "labeled statement" C++ syntax as `label: statement` to label the loops.
If there are no loops in code, leave the code unchanged.
""").strip()

prompt_fpx = dedent(
    """
## Editing Task - Arbitrary Precision and Fixed-Point Types
Your task is to modify the given user's code to convert the usage of int and uint types to arbitrary precision HLS types, `ap_int`, `ap_uint`, as well as convert float and double types to fixed-point HLS types, `ap_fixed`, provided by Vitis HLS.

- int and uint types should be converted to the appropriate arbitrary precision types, `ap_int` and `ap_uint`.
- float and double types should be converted to the appropriate fixed-point types, `ap_fixed`.

The integer types are defined as follows:
    - `ap_int<W>`: Signed integer type with `W` bits
    - `ap_uint<W>`: Unsigned integer type with `W` bits
In order to use ap_(u)int types, the user needs to include the "ap_int.h" header file.
The individual bits in the ap_(u)int types can be indexed using the [] operator.
    You can also set and clear bits at specific indexes in the ap_(u)int types using the set and clear methods:
        - void ap_(u)int::set (unsigned i)
        - void ap_(u)int::clear (unsigned i)

The fixed point type is defined as follows:
    `ap_fixed<W, I>`
where:
    - `W`: Word length in bits
    - `I`: The number of bits used to represent the integer value, that is, the number of integer bits to the left of the binary point, including the sign bit.
In order to use fixed point types, the user needs to include the "ap_fixed.h" header file.
The fixed point type can handle most C++ arithmetic operations (addition, subtraction, multiplication, division, etc.) and can be used in most C++ expressions.

If the user is also doing `cmath` operations on the original datatype numbers, these operations should be modified to use the HLS math library.
The HLS math library has the namespace `hls::*` and can be included with the following "hls_math.h" file. It supports most of the same math operators under the std::* namespace.

Typedefs for these new types are encouraged to make the code more readable.
Ideally, `typedef` statements should be placed in a header file so they can be reached by all source files.

The resulting code should maintain the same functionality as the original code but should convert all variants of int, uint, float, and double types to the appropriate arbitrary precision types.
"""
).strip()


prompt_dataflow = dedent(
    """
## Editing Task - Dataflow Semantics
Your task is to modify the given user's code to use "dataflow" semantics in the HLS kernel using the `#pragma HLS DATAFLOW` pragma.
To use this pragma effectively, the code will need to be refactored into different subfunctions for computation tasks with intermediate producers and consumer variables.
Effectively, a dataflow function only contains calls to subfunctions as well as intermediate variables passed between the subfunctions.
The subfunctions must follow single-producer single-consumer rules, meaning that a variable / buffer can only be written to by one function and then only be read by one other function.
If data is needed for two subfunctions it needs to be duplicated.

The edited kernels must not have any of the following coding styles present in order to use dataflow semantics:
- Single-producer-consumer violations
- Feedback between tasks
- Conditional execution of tasks
- Loops with multiple exit conditions

In this case, if data needs to be buffered between tasks in a dataflow region, you may consider using fixed-sized arrays as buffers.

The resulting code should maintain the same functionality as the original code but should refactor the components into necessary dataflow subfunctions and use the DATAFLOW pragma in a manner which does not cause HLS synthesis to raise any dataflow violations.
"""
).strip()

prompt_loop_tiling = dedent(
    """
## Editing Task - Loop Tiling

Your task is to refactor the user's provided HLS kernel code by applying manual loop tiling source code transformations and inserting appropriate loop unrolling and array partitioning directives to optimize parallelism and memory access efficiency.

Specifically, you should:

- Manually tile loops into smaller blocks (tiles) with constant block sizes defined in the code to improve data locality and reduce memory bandwidth bottlenecks.

For a 2D example:

```
for(int i = 0; i < N; i++) {
    for(int j = 0; j < M; j++) {
        data[i][j] = ...;
        // loop body
    }
}
```

Should be transformed into:

```
const int N_TILE = 16;
const int M_TILE = 8;

#pragma HLS array_partition variable=data cyclic factor=N_TILE dim=1
#pragma HLS array_partition variable=data cyclic factor=M_TILE dim=2
<any more array partition pragmas needed for other variables>...

for(int i = 0; i < N; i += N_TILE) {
    for(int j = 0; j < M; j += M_TILE) {
        for(int ii = 0; ii < N_TILE; ii++) {
            #pragma HLS UNROLL
            for(int jj = 0; jj < M_TILE; jj++) {
                #pragma HLS UNROLL

                data[i + ii][j + jj] = ...;
                // loop body
            }
        }
    }
}
```

The same applies to 1D loops and n-D loops. Not all dimensions need to be tiled in every application.

- All loops must have fixed bounds and be perfect loops. Any other loop type is not allowed for tiling.
- The `#pragma HLS array_partition` pragma must be used if any arrays inside the loop are accessed using the tile indexes.
- Tiling with dependec on the outer loop is NOT allowed (ex. (ii = i; ii < i + N_TILE; ii++) is not allowed)
- Insert loop unrolling pragmas (`#pragma HLS UNROLL`) in the block loop of the loop tiling to minimize loop control overhead and maximize instruction-level parallelism.
- Be sure that the tiling factor is a constant value that is a factor of the loop trip count.
- If arrays are accessed using tile indexes, you must array partitioning pragmas (`#pragma HLS ARRAY_PARTITION <type> factor=... dim=...`) to allow parallel access to array elements inside unrolled loop tiles.
    - <type> can be `block` or `cyclic`, `factor` is the partitioning factor, and `dim` is the dimension of the array to partition (indexing starting at 1).
    - If multiple dims are partitioned, each dim of the array needs a separate pragma statement.
    - `factor` can be set to a const or define value in the code.
- Ensure the transformed loops maintain the same functionality and do not introduce loop-carried dependencies or initiation interval (II) violations.

If loop tiling and unrolling optimizations are not applicable to the provided kernel code, leave the code unchanged.
"""
)


prompt_output_format_editing_xml = dedent(
    text="""
## Output Format
The generated HLS edited output code should be provided in the following format:
```
<OUTPUT_CODE name="kernel_name.h">
    ...
</OUTPUT_CODE>
<OUTPUT_CODE name="kernel_name.cpp">
    ...
</OUTPUT_CODE>
<OUTPUT_CODE name="kernel_name_tb.cpp">
    ...
</OUTPUT_CODE>
```
Please use this XML format and do not use other formats like markdown code blocks or plain text.

You must output all three code blocks: the edited kernel code, the edited header file, and the edited testbench code.
If one of the files is not edited, you still need output the code block with the original code.
In the example above `kernel_name` should be replaced with the original name of the kernel.
Make sure the testbench filename ends with `_tb.cpp`.

Only output the generated HLS code in the XML format and nothing else.
"""
).strip()


def build_prompt_edit_zero_shot(
    prompt_task: str,
    design_description_fp: Path,
    design_h: Path,
    design_kernel: Path,
    design_tb: Path,
) -> str:
    p = prompt_pre
    p += "\n\n"
    p += prompt_edit
    p += "\n\n"
    p += prompt_task
    p += "\n\n"
    p += prompt_output_format_editing_xml
    p += "\n\n"

    p += "## Task Inputs\n"
    p += "\n"
    code = build_input_code_prompt_xml(
        {
            design_description_fp.name: design_description_fp.read_text(),
            design_h.name: design_h.read_text(),
            design_kernel.name: design_kernel.read_text(),
            design_tb.name: design_tb.read_text(),
        }
    )
    p += code
    p += "\n\n"

    p += "## Task Output\n"
    p += "\n"

    return p


prompt_pre_agent = dedent(
    """
## Overview
You are a helpful export hardware engineer and software developer who will assist the user with hardware design tasks for high-level synthesis.
The task will center around high-level synthesis (HLS) code written in C++ for a hardware design. The HLS design is written to target the latest Vitis HLS tool from Xilinx, which maps C++ code to a Verilog implementation for FPGAs.
"""
).strip()

prompt_gen_agent = dedent(
    """
## Task Description
Given a natural language description of an HLS design, a pre-written C++ design header, and a pre-written C++ testbench, generate the C++ implementation of the HLS design that aligns with the natural language description of the design.

It should be functionally equivalent to the natural language description, be consistent with the provided header file, and pass the testbench. The design should also be synthesizable by the HLS tool.

Only generate the C++ code for the HLS design; do not modify the header file or the testbench.
The implemented design therefore must be consistant with the header file and testbench. 

Be sure to try and compile and run the testbench before submitting the final deliverable. You have access to a standard C++ compiler to compile and run the testbench.
If there are any compilation errors or the testbench does not run correctly, attempt to fix the issue.

The task is complete once the kernel is implemented and the testbench that calls the kernel runs correctly and returns the expected results.
"""
).strip()


prompt_organization_agent = Template(dedent(
    text="""
## Organization
You have access to the design project directory.

This directory will contain the input design files at the root level:
- `./${fn_design_description}`
- `./${fn_design_h}`
- `./${fn_design_tb}`

You many not modify any of these input files including the design description file, header file, and testbench file.
There may also be other miscellaneous files in the directory, but those are also input files that should not be modified.

Your task is to implement the HLS design itself. This should be implemented in the `./${fn_design_kernel}` file.

By the end of your task, this the kernel implemenation `./${fn_design_kernel}` must be in the root directory of the design project directory.

You may generate other files in the process of implementing the HLS design (ex. the output bin of a the compiled testbench, etc.).

Failure to follow this file organization for this task will result in a task failure.
""").strip())


def build_prompt_gen_agentic(
    fn_design_description: str,
    fn_design_h: str,
    fn_design_tb: str,
    fn_design_kernel: str,
) -> str:
    p = prompt_pre_agent
    p += "\n\n"
    p += prompt_gen_agent
    p += "\n\n"
    p += prompt_organization_agent.substitute(fn_design_description=fn_design_description, fn_design_h=fn_design_h, fn_design_tb=fn_design_tb, fn_design_kernel=fn_design_kernel)
    return p