import argparse
import logging
from pathlib import Path
from string import Template
from textwrap import dedent

from dotenv import dotenv_values

from hls_eval.llms import Model, build_model_remote_tai
from hls_eval.prompting import extract_code_from_markdown_simple
from hls_eval.utils import check_key

prompt_template_description = Template(
    dedent("""
    You are a high-level synthesis expert.
    Help me write a natural description of this high-level synthesis hardware design.

    The description should cover the algorithm and functionality as well as the high level dataflow and architecture of the design.
    Someone should be able to fully implement the design from the description provided.
    Assume the reader knows little about the design and needs a detailed explanation.
    Also include all details about any implementation quirks, edge cases, or design decisions that are important to this specific design.
    This should include any latex equations if important or relevent to the design.
           
    Include the list of top-level function inputs and outputs as well as a brief description of the functionality the kernel represents.
    All arguments in the top-level function should be described in the inputs and outputs sections with details about the data type and layout.
    Include a list of any important data structures and data types used in the design only if they are explictly listed in the code.
    Include a list of sub-components and a brief description of the functionality of each sub-component only if they are explictly listed as seperate C++ functions in the code.
    If a sub-component is not listed as a seperate C++ function, it should not be listed at all. 

    Make sure descriptions about the high-level algorithm, inputs, outputs, data structures, and sub-components are detailed and thorough and include information about implementation, data type size layout, and architecture.
    Each description can be multiple sentences long.

    Sometimes a pre-existing kernel_description.md file is provided. If so use it as a starting guide but not the final output. Try to use all the information in the pre-existing description.

    The top level kernel function is: `${top_name}`

    Only output the description in a code block representing markdown.

    The output should be formatted excatly follows with no deviation:
    ```
    Kernel Description:
    A high level natural language description of the design...
    (be detailed and thorough, can be lengthy if needed, do not omit any details, can include latex equations if important or relevent to the design)

    ---

    Top-Level Function: `name_of_top_level_function`
    
    Complete Function Signature of the Top-Level Function:
    `return_type name_of_top_level_function(input_1_type input_1, ...);`
            
    Inputs:
    - `input_1`: description of input_1...
    - ....

    Outputs:
    - `output_1`: description of output_1...
    - ....

    Important Data Structures and Data Types:
    - `data_structure_1`: description of data_structure_1... (description of the data structure, data type, size, layout, fields, use in the design, etc. are required)

    Sub-Components:
    - `subcomponent_1`:
        - Signature: `return_type subcomponent_1(input_1_type input_1, ...);`
        - Details: natural language description of subcomponent_1...
    - ...
    ```

    Optional pre-existing simple kernel_description.md file:
    
    ${existing_description}
           
    Input Kernel Code:

    ${kernel_code}

    Description in requested markdown code block format (do not provide anything other than the description in the requested format):
    """).strip()
)

code_file_template = Template(
    dedent("""
    File Name: `${file_name}`
    ```${md_code_block_type}
    ${file_contents}
    ```
    """).strip()
)


def run_description_builder(args, model: Model):
    source_dir: Path = args.source_bench_dir
    assert source_dir.exists(), f"source bench directory {source_dir} does not exist"
    source_files = list(source_dir.glob("*.cpp")) + list(source_dir.glob("*.h"))
    source_files = sorted([f for f in source_files if f.is_file()])

    if args.use_existing_description:
        existing_description_file = source_dir / "kernel_description.md"
        if existing_description_file.exists():
            existing_description = existing_description_file.read_text()
        else:
            existing_description = None
    else:
        existing_description = None

    all_code_formatted = []
    for source_file in source_files:
        c = code_file_template.substitute(
            file_name=source_file.name,
            md_code_block_type=source_file.suffix.removeprefix("."),
            file_contents=source_file.read_text(),
        )
        all_code_formatted.append(c)

    all_code = "\n\n".join(all_code_formatted)

    # find the top.txt file
    top_file = source_dir / "top.txt"
    assert top_file.exists(), f"top.txt file not found in {source_dir}"
    top_name = top_file.read_text().strip()
    assert top_name, "top.txt file is empty"

    prompt = prompt_template_description.substitute(
        top_name=top_name,
        kernel_code=all_code,
        existing_description=existing_description,
    )

    r = model.llm.prompt(prompt, temperature=args.model_temperature, stream=False)
    r._force()
    r_txt = r.text().strip()

    try:
        description_clean = extract_code_from_markdown_simple(r_txt)
    except ValueError:
        description_clean = r_txt
        if r_txt.startswith("```"):
            description_clean = r_txt.removeprefix("```").strip()
        if r_txt.endswith("```"):
            description_clean = r_txt.removesuffix("```").strip()
        description_clean = description_clean.strip()

    # check the output_dir exists
    output_dir: Path = args.output_dir
    if not output_dir.exists():
        raise FileNotFoundError(f"output directory {output_dir} does not exist")

    # write the description to a file
    output_file = output_dir / args.output_description_file_name
    output_file.write_text(description_clean)


def build_file_list_string(files: list[Path]) -> str:
    return "\n".join([f"- {f}" for f in files])


prompt_template_testbench = Template(
    dedent("""
    You are a high-level synthesis expert.
    Help me write a self contained single file testbench for this high-level synthesis hardware design.
    
    This testbench should reside in a single C++ file and should be able to be compiled and run with the design to verify the correctness of the design.
    The testbench should include a main function that calls the top-level function of the design with a set of test inputs and verifies the outputs.
    The testbench should include a set of test inputs that are representative of the expected inputs to the design.
    The testbench should include a set of expected outputs that are representative of the expected outputs of the design.
    The inputs and outputs used should be enough to verify the functionality of the design.
    
    The testbench should always return 0 if the design is correct and the testbench passes and should return a 1 if the design is incorrect and the testbench fails.

    The current code may contain a testbench code and utility code for the testbench. If so, the goal is to simplify the testbench code and make it self-contained in a single file.
    If the current code does not contain a testbench, the goal is to write a testbench from scratch that is self-contained in a single file.
    
    If the current code contains a testbench, and the testbench uses precomputed data files in the testbench as golden inputs and outputs, the generated testbench must use them.

    The top level HLS kernel function is: `${top_name}`

    Only output the testbench code in a code block representing C++. No need to add the `cpp` identifier to the code block.

    It should look like this:
        
    ```
    testbench C++ source code
    ```
           
    File List:
    ${file_list}
           
    Optional pre-existing simple kernel_description.md file:
    
    ${existing_description}
           
    Input Kernel Code:

    ${kernel_code}

    Self-contained testbench code in requested C++ code block format (do not provide anything other than the testbench code in the requested format):
    """).strip()
)


def run_testbench_builder(args, model):
    source_dir: Path = args.source_bench_dir
    assert source_dir.exists(), f"source bench directory {source_dir} does not exist"
    source_files = list(source_dir.glob("*.cpp")) + list(source_dir.glob("*.h"))
    source_files = sorted([f for f in source_files if f.is_file()])

    if args.use_existing_description:
        existing_description_file = source_dir / "kernel_description.md"
        if existing_description_file.exists():
            existing_description = existing_description_file.read_text()
        else:
            existing_description = None
    else:
        existing_description = None

    all_code_formatted = []
    for source_file in source_files:
        c = code_file_template.substitute(
            file_name=source_file.name,
            md_code_block_type=source_file.suffix.removeprefix("."),
            file_contents=source_file.read_text(),
        )
        all_code_formatted.append(c)

    all_code = "\n\n".join(all_code_formatted)

    # find the top.txt file
    top_file = source_dir / "top.txt"
    assert top_file.exists(), f"top.txt file not found in {source_dir}"
    top_name = top_file.read_text().strip()
    assert top_name, "top.txt file is empty"

    file_list = build_file_list_string(sorted(source_dir.glob("*")))

    prompt = prompt_template_testbench.substitute(
        top_name=top_name,
        kernel_code=all_code,
        existing_description=existing_description,
        file_list=file_list,
    )

    # print(file_list)
    # exit(0)

    r = model.llm.prompt(prompt, temperature=args.model_temperature, stream=False)
    r._force()
    r_txt = r.text().strip()

    try:
        tb_clean = extract_code_from_markdown_simple(r_txt)
    except ValueError:
        tb_clean = r_txt
        if r_txt.startswith("```"):
            tb_clean = r_txt.removeprefix("```").strip()
        if r_txt.endswith("```"):
            tb_clean = r_txt.removesuffix("```").strip()
        tb_clean = tb_clean.strip()

    output_dir: Path = args.output_dir
    if not output_dir.exists():
        raise FileNotFoundError(f"output directory {output_dir} does not exist")

    output_file = output_dir / args.output_testbench_file_name
    output_file.write_text(tb_clean)


prompt_list_subcomponents = Template(
    dedent(""""
    You are a high-level synthesis expert."
    Help me identify all the sub-components in this high-level synthesis hardware design."

    Given the exsigin kernel code, header, and optional description, identify all the sub-components in the design.
    A sub-component is a seperate C++ function in the code that is not the top-level function.
    This can also include sub-functions that are called by other sub-functions.
    A sub-component should be identified by the function name.
    If a sub-component is not listed as a seperate C++ function, it should not be listed at all.
           
    Output the list of sub-components in the design in a code block representing markdown.
        
    The top level HLS kernel function is: `${top_name}`
           
    Only output the list of sub-components in a code block representing markdown. Do not nest the list, just have a flat list of sub-components.
    The output should be formatted exactly follows with no deviation:
           
    ```
    - `subcomponent_1`
    - `subcomponent_2`
    - ...
    ```
           
    Optional pre-existing simple kernel_description.md file:
        
    ${existing_description}
           
    Input Kernel Code:
           
    ${kernel_code}
           
    List of Sub-Components in requested markdown code block format (do not provide anything other than the list of sub-components in the requested format):
    """).strip()
)

prompt_extract_subcomponent = Template(
    dedent(""""
    You are a high-level synthesis expert."
    Help me extract the code for a specific sub-component in this high-level synthesis hardware design."
           
    Given the exsigin kernel code, header, and optional description, extract the code for a specific sub-component in the design.
    A sub-component is a seperate C++ function in the code that is not the top-level function.
           
    The top level HLS kernel function is: `${top_name}`
    
    The sub-component to extract is: `${subcomponent_name}`
    
    Only output the code in a single C++ code block that contains the code for the sub-component and all additional code needed to compile and run the sub-component (including other sub-components called by target sub-component).
    Assume you can use the same header file and any other code in the directory to compile and run the sub-component.
    Do not include the `cpp` identifier in the markdown code block, just the code block ticks.
           
    The output should be formatted exactly follows with no deviation:
    ```
    C++ code for the sub-component...
    ```
           
    Optional pre-existing simple kernel_description.md file:
           
    ${existing_description}
           
    Input Kernel Code:
    
    ${kernel_code}
           
    Code for the Sub-Component in requested C++ code block format (do not provide anything other than the code for the sub-component in the requested format):
    """).strip()
)


def run_hierarchy_builder(args, model):
    source_dir: Path = args.source_bench_dir
    assert source_dir.exists(), f"source bench directory {source_dir} does not exist"
    source_files = list(source_dir.glob("*.cpp")) + list(source_dir.glob("*.h"))
    source_files = sorted([f for f in source_files if f.is_file()])
    all_code_formatted = []
    for source_file in source_files:
        c = code_file_template.substitute(
            file_name=source_file.name,
            md_code_block_type=source_file.suffix.removeprefix("."),
            file_contents=source_file.read_text(),
        )
        all_code_formatted.append(c)

    all_code = "\n\n".join(all_code_formatted)

    top_file = source_dir / "top.txt"
    assert top_file.exists(), f"top.txt file not found in {source_dir}"
    top_name = top_file.read_text().strip()

    if args.use_existing_description:
        existing_description_file = source_dir / "kernel_description.md"
        if existing_description_file.exists():
            existing_description = existing_description_file.read_text()
        else:
            existing_description = None
    else:
        existing_description = None

    prompt = prompt_list_subcomponents.substitute(
        top_name=top_name,
        kernel_code=all_code,
        existing_description=existing_description,
    )

    r = model.llm.prompt(prompt, temperature=args.model_temperature, stream=False)
    r._force()
    r_txt = r.text().strip()

    try:
        subcomponents_clean = extract_code_from_markdown_simple(r_txt)
    except ValueError:
        subcomponents_clean = r_txt
        if r_txt.startswith("```"):
            subcomponents_clean = r_txt.removeprefix("```").strip()
        if r_txt.endswith("```"):
            subcomponents_clean = r_txt.removesuffix("```").strip()
        subcomponents_clean = subcomponents_clean.strip()

    subcomponents = []
    for line in subcomponents_clean.splitlines():
        subcomponents.append(
            line.strip().removeprefix("- ").removeprefix("`").removesuffix("`").strip()
        )

    if not subcomponents:
        print("no subcomponents found")
        return

    output_dir: Path = args.output_dir
    if not output_dir.exists():
        raise FileNotFoundError(f"output directory {output_dir} does not exist")

    output_file = output_dir / "subcomponents.md"
    output_file.write_text(subcomponents_clean)

    for subcomponent in subcomponents:
        print(f"extracting subcomponent: {subcomponent}")
        prompt = prompt_extract_subcomponent.substitute(
            top_name=top_name,
            subcomponent_name=subcomponent,
            kernel_code=all_code,
            existing_description=existing_description,
        )

        r = model.llm.prompt(prompt, temperature=args.model_temperature, stream=False)
        r._force()
        r_txt = r.text().strip()

        try:
            subcomponent_code_clean = extract_code_from_markdown_simple(r_txt)
        except ValueError:
            subcomponent_code_clean = r_txt
            if r_txt.startswith("```"):
                subcomponent_code_clean = r_txt.removeprefix("```").strip()
            if r_txt.endswith("```"):
                subcomponent_code_clean = r_txt.removesuffix("```").strip()
            subcomponent_code_clean = subcomponent_code_clean.strip()

        output_subcomponent_dir = output_dir / args.hierarchy_sub_dir_name
        output_subcomponent_dir.mkdir(exist_ok=True)

        output_subcomponent_file = (
            output_subcomponent_dir / f"{source_dir.name}__{subcomponent}.cpp"
        )
        output_subcomponent_file.write_text(subcomponent_code_clean)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meta HLS Bench Builder Tool")

    parser.add_argument(
        "--source-bench-dir",
        type=Path,
        required=True,
        help="source bench directory",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="output directory",
    )

    parser.add_argument(
        "--model-name",
        type=str,
        required=True,
        help="source bench directory",
    )

    parser.add_argument(
        "--model-temperature",
        type=float,
        default=0.7,
        help="model temperature",
    )

    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        default="description",
        choices=["description", "testbench", "hierarchy"],
        help="mode",
    )

    parser.add_argument(
        "--output-description-file-name",
        type=str,
        default="kernel_description_generated.md",
        help="output description file name",
    )

    parser.add_argument(
        "--output-testbench-file-name",
        type=str,
        default="gen_tb.cpp",
        help="output testbench file name",
    )

    parser.add_argument(
        "--use-existing-description",
        action="store_true",
        help="use existing kernel_description.md file",
    )

    parser.add_argument(
        "--hierarchy-sub-dir-name",
        type=str,
        default="subcomponents",
        help="subcomponents directory name",
    )

    args = parser.parse_args()

    API_KEY_TOGETHERAI = check_key(dotenv_values(".env")["TOGETHER_API_KEY"])

    logger = logging.getLogger(__name__)

    logger.info(f"output-dir: {args.output_dir}")
    logger.info(f"source-bench-dir: {args.source_bench_dir}")
    logger.info(f"mode: {args.mode}")

    model = build_model_remote_tai(args.model_name, API_KEY_TOGETHERAI)

    match args.mode:
        case "description":
            run_description_builder(args, model)
        case "testbench":
            run_testbench_builder(args, model)
        case "hierarchy":
            run_hierarchy_builder(args, model)
        case _:
            raise ValueError(f"invalid mode: {args.mode}")
