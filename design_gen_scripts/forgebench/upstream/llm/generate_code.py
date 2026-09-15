import re
import random

def replace_data_type(data_type: str) -> str:
    # Replace all occurrences of <, >, and , with an underscore
    result = re.sub(r'[<>,]', '_', data_type)
    # Remove all spaces
    result = result.replace(" ", "")
    return result


# Several activation blocks in the template declare extra scalar parameters beyond
# (input, output). A config may supply its own values as func_info[2:]; otherwise
# these canonical defaults are emitted. They must stay in sync with the golden
# reference defaults in verification/activations.py.
ACTIVATION_EXTRA_PARAMS = {
    "leaky_relu": [0.01],
    "prelu": [0.25],
    "rrelu": [0.125, 1.0 / 3.0],
    "thresholded_relu": [1.0],
    "relu6": [6.0],
    "elu": [1.0],
    "selu": [1.6732632423543772, 1.0507009873554805],
}


def _activation_name(func_info):
    name = func_info[1].lower()
    return "tanh_act" if name == "tanh" else name


def activation_extra_decl(func_info, full_func_name, HIDDEN_DIM):
    """File-scope declaration an activation needs, or "".

    prelu takes `data_t alpha[HIDDEN_DIM]` (per-feature), so its coefficients are
    emitted as an array next to the function definition. `full_func_name` already
    encodes the dims and data type and is deduplicated by generate_top_function,
    so the array name is unique per emitted definition. It is deliberately not
    `const`: the template's parameter is a plain `data_t[]`.
    """
    if _activation_name(func_info) != "prelu":
        return ""
    values = [float(v) for v in func_info[2:]] or ACTIVATION_EXTRA_PARAMS["prelu"]
    if len(values) == 1:
        values = values * HIDDEN_DIM
    init = ", ".join(f"(data_t){v!r}" for v in values)
    return f"\nstatic data_t {full_func_name}_alpha[{HIDDEN_DIM}] = {{{init}}};\n"


def activation_extra_args(func_info, full_func_name):
    """Literal call arguments for an activation's extra parameters."""
    name = _activation_name(func_info)
    if name == "prelu":
        return [f"{full_func_name}_alpha"]
    values = list(func_info[2:]) or ACTIVATION_EXTRA_PARAMS.get(name, [])
    return [f"(data_t){float(v)!r}" for v in values]


def generate_activation_function(
    template_path,   # Path to the activation template file (e.g., activations_template_2d.cpp)
    func_name,       # The activation function to generate (e.g., "relu6", "sigmoid", "gelu", etc.)
    DATA_TYPE="float",
    SEQ_LENGTH=128,
    HIDDEN_DIM=512
):
    """
    Reads the 2D activation function template and substitutes common placeholders:
       {DATA_TYPE}, {SEQ_LENGTH}, and {HIDDEN_DIM}.
    Then extracts the function block corresponding to the specified activation (func_name)
    and writes it to output_path.
    
    Supported func_name values (case-insensitive):
      "relu", "leaky_relu", "prelu", "rrelu", "thresholded_relu", "relu6",
      "sigmoid", "tanh_act", "elu", "selu", "gelu", "swish", "softmax".
    """
    # 1) Read the full template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # 2) Substitute common placeholders.
    formatted_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH=SEQ_LENGTH,
        HIDDEN_DIM=HIDDEN_DIM
    )
    
    # 3) Determine marker strings based on the specified activation function.
    func_name = func_name.lower()  # Normalize to lower-case
    marker_start = ""
    marker_end = ""
    
    if func_name == "relu":
        marker_start = "/*==== RELU FUNCTION START ====*/"
        marker_end = "/*==== RELU FUNCTION END ====*/"
    elif func_name == "leaky_relu":
        marker_start = "/*==== LEAKY_RELU FUNCTION START ====*/"
        marker_end = "/*==== LEAKY_RELU FUNCTION END ====*/"
    elif func_name == "prelu":
        marker_start = "/*==== PRELU FUNCTION START ====*/"
        marker_end = "/*==== PRELU FUNCTION END ====*/"
    elif func_name == "rrelu":
        marker_start = "/*==== RRELU FUNCTION START ====*/"
        marker_end = "/*==== RRELU FUNCTION END ====*/"
    elif func_name == "thresholded_relu":
        marker_start = "/*==== THRESHOLDED_RELU FUNCTION START ====*/"
        marker_end = "/*==== THRESHOLDED_RELU FUNCTION END ====*/"
    elif func_name == "relu6":
        marker_start = "/*==== RELU6 FUNCTION START ====*/"
        marker_end = "/*==== RELU6 FUNCTION END ====*/"
    elif func_name == "sigmoid":
        marker_start = "/*==== SIGMOID FUNCTION START ====*/"
        marker_end = "/*==== SIGMOID FUNCTION END ====*/"
    elif func_name in ("tanh", "tanh_act"):
        # The template defines the block as tanh_act (plain `tanh` would clash with
        # C's tanh), but configs are written either way; accept both spellings.
        marker_start = "/*==== TANH FUNCTION START ====*/"
        marker_end = "/*==== TANH FUNCTION END ====*/"
    elif func_name == "elu":
        marker_start = "/*==== ELU FUNCTION START ====*/"
        marker_end = "/*==== ELU FUNCTION END ====*/"
    elif func_name == "selu":
        marker_start = "/*==== SELU FUNCTION START ====*/"
        marker_end = "/*==== SELU FUNCTION END ====*/"
    elif func_name == "gelu":
        marker_start = "/*==== GELU FUNCTION START ====*/"
        marker_end = "/*==== GELU FUNCTION END ====*/"
    elif func_name == "swish":
        marker_start = "/*==== SWISH FUNCTION START ====*/"
        marker_end = "/*==== SWISH FUNCTION END ====*/"
    elif func_name == "softmax":
        marker_start = "/*==== SOFTMAX FUNCTION START ====*/"
        marker_end = "/*==== SOFTMAX FUNCTION END ====*/"
    else:
        raise ValueError("Invalid function name. Choose one of: relu, leaky_relu, prelu, rrelu, thresholded_relu, relu6, sigmoid, tanh_act, elu, selu, gelu, swish, softmax.")
    
    # 4) Extract the specified function block.
    start_idx = formatted_code.find(marker_start)
    end_idx = formatted_code.find(marker_end)
    if start_idx == -1 or end_idx == -1:
        raise ValueError("Could not find the specified function markers in the template.")
    
    # Skip marker text.
    function_block = formatted_code[start_idx + len(marker_start): end_idx].strip()
    
    DATA_TYPE = replace_data_type(DATA_TYPE)
    dim_suffix = f"_{SEQ_LENGTH}_{HIDDEN_DIM}_{DATA_TYPE}"
    # Use a regex to capture "void" followed by the function name. Record the
    # template's actual name so the generated call matches the emitted
    # definition: some blocks are named differently from the config's activation
    # string (e.g. tanh is defined as tanh_act to avoid clashing with C's tanh).
    captured_name = []

    def _append_dim_suffix(m):
        captured_name.append(m.group(2))
        return m.group(1) + dim_suffix + "("

    function_block = re.sub(
        r"(void\s+(\w+))\s*\(",
        _append_dim_suffix,
        function_block,
        count=1
    )

    # 5) Optionally, include a header (everything before the first marker).
    header_end = formatted_code.find("/*====")
    header = ""
    if header_end != -1:
        header = formatted_code[:header_end].strip() + "\n\n"

    output_code = header + function_block

    emitted_name = captured_name[0] if captured_name else func_name
    return output_code, emitted_name + dim_suffix
    



def generate_load_function(
    dims,              # List of dimensions, e.g., [32, 64, 64]
    data_type="float", # Underlying data type
    func_prefix="load" # Function prefix (will be appended with dims and data_type)
):
    """
    Generates an HLS C function that copies an input array to an output array.
    The function is for arrays of dimensions given in the list 'dims'.
    
    The generated function will have a name of the form:
      <func_prefix>_<dim1>_<dim2>_..._<dimN>_data_t
    
    Parameters:
      dims: list of integers, e.g., [32, 64, 64]
      data_type: string, e.g., "float" (used in typedef and function signature)
      func_prefix: prefix for the function name (default "load")
    
    Returns:
      A string with the generated HLS C code.
    """
    # Construct the typedef and include lines
    code_lines = []
    
    
    #code_lines.append(f"typedef {data_type} data_t;\n")
    
    # Build array dimension string, e.g., "[32][64][64]"
    array_dims = "".join(f"[{d}]" for d in dims)
    
    # Construct the function name. E.g., load_32_64_64_data_t
    dim_suffix = "_".join(str(d) for d in dims)
    
    data_type = replace_data_type(data_type)
    func_name = f"{func_prefix}_{dim_suffix}_{data_type}"
    
    # Build function signature
    code_lines.append(f"void {func_name}(data_t input{array_dims}, data_t output{array_dims})")
    code_lines.append("{")
    
    # Generate nested loops.
    # We'll name the loop indices based on the dimension order: idx0, idx1, ..., idxN.
    indent = "    "
    for idx, d in enumerate(dims):
        code_lines.append(f"{indent * (idx+1)}for (int idx{idx} = 0; idx{idx} < {d}; idx{idx}++) {{")
    
    # Generate the assignment line.
    # Build index strings for input and output, e.g., [idx0][idx1][idx2]
    index_str = "".join(f"[idx{idx}]" for idx in range(len(dims)))
    code_lines.append(f"{indent * (len(dims)+1)}output{index_str} = input{index_str};")
    
    # Close all for loops
    for idx in range(len(dims)-1, -1, -1):
        code_lines.append(f"{indent * (idx+1)}}}")
    
    code_lines.append("}")
    
    return "\n".join(code_lines), func_name


def generate_store_function(
    dims,              # List of dimensions, e.g., [32, 64, 64]
    data_type="float", # Underlying data type
    func_prefix="store" # Function prefix (will be appended with dims and data_type)
):
    """
    Generates an HLS C function that copies an input array to an output array.
    The function is for arrays of dimensions given in the list 'dims'.
    
    The generated function will have a name of the form:
      <func_prefix>_<dim1>_<dim2>_..._<dimN>_data_t
    
    Parameters:
      dims: list of integers, e.g., [32, 64, 64]
      data_type: string, e.g., "float" (used in typedef and function signature)
      func_prefix: prefix for the function name (default "load")
    
    Returns:
      A string with the generated HLS C code.
    """
    # Construct the typedef and include lines
    code_lines = []
    #code_lines.append(f"typedef {data_type} data_t;\n")
    
    # Build array dimension string, e.g., "[32][64][64]"
    array_dims = "".join(f"[{d}]" for d in dims)
    
    # Construct the function name. E.g., load_32_64_64_data_t
    dim_suffix = "_".join(str(d) for d in dims)
    data_type = replace_data_type(data_type)
    func_name = f"{func_prefix}_{dim_suffix}_{data_type}"
    
    # Build function signature
    code_lines.append(f"void {func_name}(data_t input{array_dims}, data_t output{array_dims})")
    code_lines.append("{")
    
    # Generate nested loops.
    # We'll name the loop indices based on the dimension order: idx0, idx1, ..., idxN.
    indent = "    "
    for idx, d in enumerate(dims):
        code_lines.append(f"{indent * (idx+1)}for (int idx{idx} = 0; idx{idx} < {d}; idx{idx}++) {{")
    
    # Generate the assignment line.
    # Build index strings for input and output, e.g., [idx0][idx1][idx2]
    index_str = "".join(f"[idx{idx}]" for idx in range(len(dims)))
    code_lines.append(f"{indent * (len(dims)+1)}output{index_str} = input{index_str};")
    
    # Close all for loops
    for idx in range(len(dims)-1, -1, -1):
        code_lines.append(f"{indent * (idx+1)}}}")
    
    code_lines.append("}")
    
    return "\n".join(code_lines), func_name


def generate_layer_norm_code(
    template_path,    # Path to layer_norm_template.cpp
    DATA_TYPE="float",
    SEQ_LENGTH=128,   # e.g., sequence length
    DIM=512,          # e.g., feature dimension
    EPSILON=1e-5      # e.g., epsilon value
):
    """
    Reads the layer norm template file and substitutes placeholders with the provided parameters.
    The expected placeholders in the template are:
       {DATA_TYPE}, {SEQ_LENGTH}, {DIM}, and {EPSILON}.
       
    Generates the final HLS C code and writes it to output_path.
    """
    # 1) Read the template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # 2) Substitute placeholders.
    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH=SEQ_LENGTH,
        DIM=DIM,
        EPSILON=EPSILON
    )
    
    DATA_TYPE = replace_data_type(DATA_TYPE)
    dim_suffix = f"_{SEQ_LENGTH}_{DIM}_{DATA_TYPE}"
    func_name = "layer_norm" + dim_suffix
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+layer_norm)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    return new_generated_code, func_name
    
    
def generate_rms_norm_code(
    template_path,    # Path to rms_norm_template.cpp
    DATA_TYPE="float",
    SEQ_LENGTH=128,   # e.g., sequence length (number of rows)
    DIM=512,          # e.g., feature dimension (number of columns)
    EPSILON=1e-5      # small constant to avoid division by zero
):
    """
    Reads the RMSNorm template file and substitutes placeholders with the provided parameters.
    Expected placeholders in the template:
      {DATA_TYPE}, {SEQ_LENGTH}, {DIM}, {EPSILON}.
      
    Generates the final HLS C code and writes it to output_path.
    """
    # 1) Read the template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # 2) Substitute placeholders.
    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH=SEQ_LENGTH,
        DIM=DIM,
        EPSILON=EPSILON
    )
    
    DATA_TYPE = replace_data_type(DATA_TYPE)
    dim_suffix = f"_{SEQ_LENGTH}_{DIM}_{DATA_TYPE}"
    func_name = "rms_norm" + dim_suffix
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+rms_norm)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    return new_generated_code, func_name


def generate_matmul_code(
    template_path,   # Path to matmul_template.cpp
    DATA_TYPE="float",
    SEQ_LENGTH=128,
    DIM_IN=512,
    DIM_OUT=256,
    use_bias=False
):
    """
    Reads the matrix multiplication template and substitutes placeholders.
    The template expects the following placeholders:
       {DATA_TYPE}, {SEQ_LENGTH}, {DIM_IN}, {DIM_OUT}, {BIAS_ARG}, and {INIT_VAL}.
    
    If use_bias is True:
       - {BIAS_ARG} becomes: "    data_t bias[{DIM_OUT}],\n"
       - {INIT_VAL} becomes: "bias[j]"
    Otherwise:
       - {BIAS_ARG} becomes an empty string.
       - {INIT_VAL} becomes: "((data_t)0)"
    """
    # Read the template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # Build bias-related placeholders.
    if use_bias:
        bias_arg = "    data_t bias[{DIM_OUT}],\n".format(DIM_OUT=DIM_OUT)
        init_val = "bias[j]"
    else:
        bias_arg = ""
        init_val = "((data_t)0)"
    
    # Substitute placeholders in the template.
    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH=SEQ_LENGTH,
        DIM_IN=DIM_IN,
        DIM_OUT=DIM_OUT,
        BIAS_ARG=bias_arg,
        INIT_VAL=init_val
    )
    
    DATA_TYPE = replace_data_type(DATA_TYPE)
    if use_bias == True:
        dim_suffix = f"_{SEQ_LENGTH}_{DIM_IN}_{DIM_OUT}_bias_{DATA_TYPE}"
    else:
        dim_suffix = f"_{SEQ_LENGTH}_{DIM_IN}_{DIM_OUT}_{DATA_TYPE}"
    func_name = "matmul" + dim_suffix
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+matmul)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    return new_generated_code, func_name
    

def generate_dropout_code(
    template_path,    # Path to dropout_template.cpp
    DATA_TYPE="float",
    SEQ_LENGTH=128,
    DIM=512
):
    """
    Reads the dropout template and substitutes placeholders with provided parameters.
    
    Expected placeholders in the template:
      {DATA_TYPE}, {SEQ_LENGTH}, {DIM}
      
    Generates the final HLS C code for the dropout function and writes it to output_path.
    """
    # 1) Read the template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # 2) Substitute placeholders.
    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH=SEQ_LENGTH,
        DIM=DIM
    )
    
    DATA_TYPE = replace_data_type(DATA_TYPE)
    dim_suffix = f"_{SEQ_LENGTH}_{DIM}_{DATA_TYPE}"
    func_name = "dropout" + dim_suffix
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+dropout)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    return new_generated_code, func_name
    
    
def generate_grouped_mha_code(
    template_path,
    DATA_TYPE="float",
    SEQ_LENGTH=128,
    DIM_IN=512,
    NUM_HEADS=8,
    HEAD_DIM=64,
    use_rope=True
):
    DIM_OUT = NUM_HEADS * HEAD_DIM

    if use_rope:
        rope_inline = f"""
    // Inline RoPE logic
    for (int seq = 0; seq < {SEQ_LENGTH}; seq++) {{
        for (int h = 0; h < {NUM_HEADS}; h++) {{
            for (int d = 0; d < {HEAD_DIM}; d += 2) {{
                int idx = h * {HEAD_DIM} + d;
                data_t theta = (data_t)hls::powf(10000.0f, -((float)d) / (float){HEAD_DIM});
                data_t angle = seq * theta;
                data_t cos_val = hls::cos(angle);
                data_t sin_val = hls::sin(angle);

                // Apply RoPE to Q
                data_t q0 = Q[seq][idx];
                data_t q1 = Q[seq][idx + 1];
                Q[seq][idx]     = q0 * cos_val - q1 * sin_val;
                Q[seq][idx + 1] = q0 * sin_val + q1 * cos_val;

                // Apply RoPE to K
                data_t k0 = K[seq][idx];
                data_t k1 = K[seq][idx + 1];
                K[seq][idx]     = k0 * cos_val - k1 * sin_val;
                K[seq][idx + 1] = k0 * sin_val + k1 * cos_val;
            }}
        }}
    }}"""
    else:
        rope_inline = ''

    # Read template
    with open(template_path, "r") as f:
        template_code = f.read()

    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH=SEQ_LENGTH,
        DIM_IN=DIM_IN,
        DIM_OUT=DIM_OUT,
        NUM_HEADS=NUM_HEADS,
        HEAD_DIM=HEAD_DIM,
        ROPE_INLINE=rope_inline
    )

    DATA_TYPE = replace_data_type(DATA_TYPE)
    if use_rope == True:
        dim_suffix = f"_{SEQ_LENGTH}_{DIM_IN}_{NUM_HEADS}_{HEAD_DIM}_rope_{DATA_TYPE}"
    else:
        dim_suffix = f"_{SEQ_LENGTH}_{DIM_IN}_{NUM_HEADS}_{HEAD_DIM}_{DATA_TYPE}"
    func_name = "grouped_multihead_attention" + dim_suffix
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+grouped_multihead_attention)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    return new_generated_code, func_name


def generate_sliding_window_attention_code(
    template_path,
    DATA_TYPE="float",
    SEQ_LENGTH=128,
    DIM_IN=512,
    NUM_HEADS=8,
    HEAD_DIM=64,
    use_rope=True
):
    DIM_OUT = NUM_HEADS * HEAD_DIM

    if use_rope:
        rope_inline = f"""
    // Inline RoPE logic
    for (int seq = 0; seq < {SEQ_LENGTH}; seq++) {{
        for (int h = 0; h < {NUM_HEADS}; h++) {{
            for (int d = 0; d < {HEAD_DIM}; d += 2) {{
                int idx = h * {HEAD_DIM} + d;
                data_t theta = (data_t)hls::powf(10000.0f, -((float)d) / (float){HEAD_DIM});
                data_t angle = seq * theta;
                data_t cos_val = hls::cos(angle);
                data_t sin_val = hls::sin(angle);

                // Apply RoPE to Q
                data_t q0 = Q[seq][idx];
                data_t q1 = Q[seq][idx + 1];
                Q[seq][idx]     = q0 * cos_val - q1 * sin_val;
                Q[seq][idx + 1] = q0 * sin_val + q1 * cos_val;

                // Apply RoPE to K
                data_t k0 = K[seq][idx];
                data_t k1 = K[seq][idx + 1];
                K[seq][idx]     = k0 * cos_val - k1 * sin_val;
                K[seq][idx + 1] = k0 * sin_val + k1 * cos_val;
            }}
        }}
    }}"""
    else:
        rope_inline = ''

    # Read template
    with open(template_path, "r") as f:
        template_code = f.read()

    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH=SEQ_LENGTH,
        DIM_IN=DIM_IN,
        DIM_OUT=DIM_OUT,
        NUM_HEADS=NUM_HEADS,
        HEAD_DIM=HEAD_DIM,
        ROPE_INLINE=rope_inline
    )

    DATA_TYPE = replace_data_type(DATA_TYPE)
    if use_rope == True:
        dim_suffix = f"_{SEQ_LENGTH}_{DIM_IN}_{NUM_HEADS}_{HEAD_DIM}_rope_{DATA_TYPE}"
    else:
        dim_suffix = f"_{SEQ_LENGTH}_{DIM_IN}_{NUM_HEADS}_{HEAD_DIM}_{DATA_TYPE}"
    func_name = "sliding_window_attention" + dim_suffix
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+sliding_window_attention)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    return new_generated_code, func_name


def generate_matrix_add_code(
    template_path,    # Path to matrix_add_template.cpp
    DATA_TYPE="float",
    SEQ_LENGTH=64,
    DIM=64
):
    """
    Reads the matrix addition template and substitutes the placeholders with the provided parameters.
    The template uses the following placeholders:
       {DATA_TYPE}, {C}, {H}, {W}
    
    The final function has the following signature:
       void matrix_add(data_t in1[C][H][W], data_t in2[C][H][W], data_t out[C][H][W])
    
    Parameters:
       template_path: path to the matrix_add_template.cpp file.
       output_path: path to output the generated C code.
       DATA_TYPE: the C data type for the operation (e.g., "float").
       C: number of channels.
       H: height.
       W: width.
    """
    # Read the template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # Substitute the placeholders.
    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH = SEQ_LENGTH,
        DIM = DIM
    )
    
    DATA_TYPE = replace_data_type(DATA_TYPE)
    dim_suffix = f"_{SEQ_LENGTH}_{DIM}_{DATA_TYPE}"
    
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+matrix_add)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    func_name = "matrix_add" + dim_suffix
    
    return new_generated_code, func_name
    
def generate_elementwise_mult_code(
    template_path,    # Path to matrix_add_template.cpp
    DATA_TYPE="float",
    SEQ_LENGTH=64,
    DIM=64
):
    """
    Reads the matrix addition template and substitutes the placeholders with the provided parameters.
    The template uses the following placeholders:
       {DATA_TYPE}, {C}, {H}, {W}
    
    The final function has the following signature:
       void elementwise_mult(data_t in1[C][H][W], data_t in2[C][H][W], data_t out[C][H][W])
    
    Parameters:
       template_path: path to the elementwise_mult_template.cpp file.
       output_path: path to output the generated C code.
       DATA_TYPE: the C data type for the operation (e.g., "float").
       C: number of channels.
       H: height.
       W: width.
    """
    # Read the template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # Substitute the placeholders.
    generated_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        SEQ_LENGTH = SEQ_LENGTH,
        DIM = DIM
    )
    
    DATA_TYPE = replace_data_type(DATA_TYPE)
    dim_suffix = f"_{SEQ_LENGTH}_{DIM}_{DATA_TYPE}"
    
    # Use regex to capture the function signature of maxpool.
    # We assume the template defines the function starting with "void maxpool(".
    new_generated_code = re.sub(
        r"(void\s+elementwise_mult)\s*\(",
        lambda m: m.group(1) + dim_suffix + "(",
        generated_code,
        count=1
    )
    
    func_name = "elementwise_mult" + dim_suffix
    
    return new_generated_code, func_name
    
 

def generate_func_def(op_info, data_type):
    
    if op_info['func_name'] == 'load':
        code_line, full_func_name = generate_load_function(op_info["dims"], data_type, func_prefix="load")
    elif op_info['func_name'] == 'store':
        code_line, full_func_name = generate_store_function(op_info["dims"], data_type, func_prefix="store")
    elif op_info['func_name'] == 'matmul':
        code_line, full_func_name = generate_matmul_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1], op_info["dims"][2], op_info["func_info"][1])
    elif op_info['func_name'] == 'mha':
        code_line, full_func_name = generate_grouped_mha_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1], op_info["dims"][2], op_info["dims"][3], op_info["func_info"][1])
    elif op_info['func_name'] == 'swa':
        code_line, full_func_name = generate_sliding_window_attention_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1], op_info["dims"][2], op_info["dims"][3], op_info["func_info"][1])
    elif op_info['func_name'] == 'layernorm':
        code_line, full_func_name = generate_layer_norm_code(op_info["func_info"][0], data_type,  op_info["dims"][0], op_info["dims"][1], op_info["dims"][2])
    elif op_info['func_name'] == 'rmsnorm':
        code_line, full_func_name = generate_rms_norm_code(op_info["func_info"][0], data_type,  op_info["dims"][0], op_info["dims"][1], op_info["dims"][2])
    elif op_info['func_name'] == 'activation':
        code_line, full_func_name = generate_activation_function(op_info["func_info"][0], op_info["func_info"][1], data_type,  op_info["dims"][0], op_info["dims"][1])
        code_line += activation_extra_decl(op_info["func_info"], full_func_name, op_info["dims"][1])
    elif op_info['func_name'] == 'dropout':
        code_line, full_func_name = generate_dropout_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1])
    elif op_info['func_name'] == 'matrix_add':
        code_line, full_func_name = generate_matrix_add_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1])
    elif op_info['func_name'] == 'elementwise_mult':
        code_line, full_func_name = generate_elementwise_mult_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1]) 
    else:
        print("the operator we do not support!")
        
    return code_line, full_func_name


def generate_operator_call(op_info, data_type):
    """
    Generates a single function call string given an operator dictionary.
    
    op_info: dict with keys:
       - "func_name": base function name (e.g., "load", "conv2d", etc.)
       - "dims": list of integers (e.g., [32,64,64] or [32,64,64,32,64,64])
       - "args": list of argument strings for the function call
       
    Returns a string like:
       load_32_64_64_data_t(DRAM_1, BRAM_1);
    """

    if op_info['func_name'] == 'load':
        code_line, full_func_name = generate_load_function(op_info["dims"], data_type, func_prefix="load")
    elif op_info['func_name'] == 'store':
        code_line, full_func_name = generate_store_function(op_info["dims"], data_type, func_prefix="store")
    elif op_info['func_name'] == 'matmul':
        code_line, full_func_name = generate_matmul_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1], op_info["dims"][2], op_info["func_info"][1])
    elif op_info['func_name'] == 'mha':
        code_line, full_func_name = generate_grouped_mha_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1], op_info["dims"][2], op_info["dims"][3], op_info["func_info"][1])
    elif op_info['func_name'] == 'swa':
        code_line, full_func_name = generate_sliding_window_attention_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1], op_info["dims"][2], op_info["dims"][3], op_info["func_info"][1])
    elif op_info['func_name'] == 'layernorm':
        code_line, full_func_name = generate_layer_norm_code(op_info["func_info"][0], data_type,  op_info["dims"][0], op_info["dims"][1], op_info["dims"][2])
    elif op_info['func_name'] == 'rmsnorm':
        code_line, full_func_name = generate_rms_norm_code(op_info["func_info"][0], data_type,  op_info["dims"][0], op_info["dims"][1], op_info["dims"][2])
    elif op_info['func_name'] == 'activation':
        code_line, full_func_name = generate_activation_function(op_info["func_info"][0], op_info["func_info"][1], data_type,  op_info["dims"][0], op_info["dims"][1])
        code_line += activation_extra_decl(op_info["func_info"], full_func_name, op_info["dims"][1])
    elif op_info['func_name'] == 'dropout':
        code_line, full_func_name = generate_dropout_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1])
    elif op_info['func_name'] == 'matrix_add':
        code_line, full_func_name = generate_matrix_add_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1])
    elif op_info['func_name'] == 'elementwise_mult':
        code_line, full_func_name = generate_elementwise_mult_code(op_info["func_info"][0], data_type, op_info["dims"][0], op_info["dims"][1])
    else:
        print("the operator we do not support!")

    extra_args = (activation_extra_args(op_info["func_info"], full_func_name)
                  if op_info['func_name'] == 'activation' else [])
    args_str = ", ".join(list(op_info["args"]) + extra_args)
    return f"{full_func_name}({args_str});"
    
    
def generate_top_function(brams, drams, ops, data_type="float", top_func_name="top"):
    """
    Generates the complete HLS C top function.
    
    Parameters:
      - brams: list of dicts for BRAM arrays. Each dict has:
           "name": string, array name.
           "dims": list of ints for dimensions.
      - drams: list of dicts for DRAM arrays used in the top function. Each dict has:
           "name": string, array name.
           "dims": list of ints for dimensions.
           "bundle": string, the bundle name for the HLS interface pragma.
      - ops: a dictionary (or ordered dict) where each key is an operator name 
             (for ordering) and the value is a dict with keys "func_name", "dims", "args".
      - data_type: the C data type for data_t.
      - top_func_name: name of the top function.
      
    Returns a string containing the generated HLS C code.
    """
    code_lines = []
    
    code_lines.append("")
    code_lines.append(f"#include <stdio.h>")
    code_lines.append(f"#include <iostream>")
    code_lines.append(f"#include <fstream>")
    code_lines.append(f"#include <cstdlib>")
    code_lines.append(f"#include <ap_fixed.h>")
    code_lines.append(f"#include <hls_math.h>")
    code_lines.append(f"#include <stdlib.h>")
    code_lines.append(f"#include <cstdint>")
    code_lines.append(f"#include <hls_math.h>")
    code_lines.append(f"using namespace std;\n")
    
    # 1. Write typedef.
    code_lines.append(f"typedef {data_type} data_t;\n")
    
    # 2. Declare BRAM arrays.
    for bram in brams:
        dims_str = "".join(f"[{d}]" for d in bram["dims"])
        code_lines.append(f"data_t {bram['name']}{dims_str};")
    
    code_lines.append("")  # blank line
    
    func_name_set = set()
    func_def_name_list = []
   
    for key, op_info in ops.items():
       func_def_code, func_name  = generate_func_def(op_info, data_type)
       if func_name not in func_name_set:
           func_name_set.add(func_name)
           code_lines.append(func_def_code)
           code_lines.append("")
           func_def_name_list.append(func_name)
    
    # 3. Build the top function signature with DRAM parameters.
    dram_params = []
    for dram in drams:
        dims_str = "".join(f"[{d}]" for d in dram["dims"])
        dram_params.append(f"data_t {dram['name']}{dims_str}")
    params_str = ", ".join(dram_params)
    code_lines.append(f"void {top_func_name}({params_str})")
    code_lines.append("{")
    
    # 4. Insert the #pragma HLS interface lines for each DRAM.
    for dram in drams:
        code_lines.append(f"    #pragma HLS interface m_axi port={dram['name']} offset=slave bundle={dram['bundle']}")
    
    code_lines.append("")  # blank line before function calls
    
    # 5. Generate the operator function calls.
    # If ops is a dictionary, we iterate in insertion order.
    for key, op_info in ops.items():
        #print("the value of key is:", key)
        call_str = generate_operator_call(op_info, data_type)
        code_lines.append(f"    {call_str}")
    
    code_lines.append("}")
    
    return "\n".join(code_lines)

def prod(lst):
    """Return the product of all elements in the list."""
    result = 1
    for x in lst:
        result *= x
    return result

def generate_top_h(drams, data_type="float", top_func_name="top"):
    """
    Generates a top.h header file that declares the top function.
    
    Parameters:
      - drams: list of dictionaries for DRAM arrays. Each dict must have:
           "name": string (e.g., "DRAM_1"),
           "dims": list of integers.
      - data_type: string for data type (e.g., "float").
      - top_func_name: name of the top function.
    
    Returns:
      A string containing the header file content.
    """
    lines = []
    lines.append("#include <ap_fixed.h>")
    lines.append("#ifndef TOP_H")
    lines.append("#define TOP_H")
    lines.append("")
    lines.append(f"typedef {data_type} data_t;")
    lines.append("")
    
    # Build function parameter list for DRAM arrays.
    params = []
    for dram in drams:
        dims_str = "".join(f"[{d}]" for d in dram["dims"])
        params.append(f"data_t {dram['name']}{dims_str}")
    param_str = ", ".join(params)
    lines.append(f"void {top_func_name}({param_str});")
    lines.append("")
    lines.append("#endif // TOP_H")
    
    return "\n".join(lines)

def generate_testbench_code(drams, output_dram_names, data_type="float", top_func_name="top"):
    """
    Generates a C test bench for HLS that:
      - Declares DRAM arrays using the specified dimensions.
      - Loads initial values from text files (named "<DRAM_name>.txt").
      - Calls the top function.
      - Writes the output of the DRAM(s) specified in output_dram_names to separate output files.
    
    Parameters:
      - drams: list of dictionaries for DRAM arrays. Each dict must have:
            "name": string (e.g., "DRAM_1"),
            "dims": list of integers,
            "bundle": string (used in the interface pragma).
      - output_dram_names: list of strings; each is the name of a DRAM whose contents should be printed.
      - data_type: string representing the data type (e.g., "float").
      - top_func_name: name of the top function.
      
    Returns:
      A string containing the complete C test bench code.
    """
    code_lines = []
    # Include headers.
    code_lines.append('#include <stdio.h>')
    code_lines.append('#include <stdlib.h>')
    code_lines.append('#include <math.h>')
    code_lines.append("#include <ap_fixed.h>")
    code_lines.append('#include "top.h"  // Include the top function declaration')
    code_lines.append("")

    # Golden-reference comparison tolerance (overridable at compile time).
    code_lines.append("#ifndef VERIF_RTOL")
    code_lines.append("#define VERIF_RTOL 1e-3")
    code_lines.append("#endif")
    code_lines.append("#ifndef VERIF_ATOL")
    code_lines.append("#define VERIF_ATOL 1e-5")
    code_lines.append("#endif")
    code_lines.append("#ifndef VERIF_ATOL_SCALE")
    code_lines.append("#define VERIF_ATOL_SCALE 5e-5")
    code_lines.append("#endif")
    code_lines.append("")

    # Define data type.
    code_lines.append(f"typedef {data_type} data_t;")
    code_lines.append("")
    
    # Declare DRAM arrays.
    for dram in drams:
        dims_str = "".join(f"[{d}]" for d in dram["dims"])
        code_lines.append(f"data_t {dram['name']}{dims_str};")
    code_lines.append("")
    
    # Helper function to load a text file into an array.
    code_lines.append("void load_txt_to_array(const char *filename, data_t *array, int total_size) {")
    code_lines.append("    FILE *fp = fopen(filename, \"r\");")
    code_lines.append("    if (fp == NULL) {")
    code_lines.append("        printf(\"Failed to open %s\\n\", filename);")
    code_lines.append("        exit(1);")
    code_lines.append("    }")
    code_lines.append("    for (int i = 0; i < total_size; i++) {")
    code_lines.append("        float temp;")
    code_lines.append("        fscanf(fp, \"%f\", &temp);")
    code_lines.append("        array[i] = (data_t)temp;")
    code_lines.append("    }")
    code_lines.append("    fclose(fp);")
    code_lines.append("}")
    code_lines.append("")
    
    # Main function.
    code_lines.append("int main() {")
    
    # For each DRAM, generate a load call.
    for dram in drams:
        total_elements = prod(dram["dims"])
        code_lines.append(f"    load_txt_to_array(\"{dram['name']}.txt\", (data_t*){dram['name']}, {total_elements});")
    code_lines.append("")
    
    # Insert top function call. DRAM arguments in the order of the drams list.
    dram_args = ", ".join(d["name"] for d in drams)
    code_lines.append(f"    {top_func_name}({dram_args});")
    code_lines.append("")

    # Golden-reference verification accumulators.
    code_lines.append("    double verif_max_abs = 0.0, verif_max_rel = 0.0;")
    code_lines.append("    long verif_n_mismatch = 0, verif_n_total = 0, verif_n_checked = 0;")
    code_lines.append("")

    # For each output DRAM specified in output_dram_names, dump then compare.
    for out_name in output_dram_names:
        # Find the DRAM in the configuration.
        matched = None
        for dram in drams:
            if dram["name"] == out_name:
                matched = dram
                break
        if matched is None:
            raise ValueError(f"Output DRAM {out_name} not found in DRAM configuration.")
        total_out = prod(matched["dims"])
        # Keep the existing output dump for debugging.
        code_lines.append(f"    // Write contents of {out_name} to {out_name}_output.txt")
        code_lines.append("    {")
        code_lines.append(f"        FILE *fp = fopen(\"{out_name}_output.txt\", \"w\");")
        code_lines.append("        if (fp != NULL) {")
        code_lines.append(f"            for (int i = 0; i < {total_out}; i++) {{")
        code_lines.append(f"                fprintf(fp, \"%f \", (float)((data_t*){out_name})[i]);")
        code_lines.append("            }")
        code_lines.append("            fclose(fp);")
        code_lines.append("        }")
        code_lines.append("    }")
        # Compare against the golden file if present (backward compatible if absent).
        code_lines.append(f"    // Compare {out_name} against {out_name}.golden.txt if present")
        code_lines.append("    {")
        code_lines.append(f"        FILE *gf = fopen(\"{out_name}.golden.txt\", \"r\");")
        code_lines.append("        if (gf != NULL) {")
        # Two passes: the absolute tolerance is scaled by the output tensor's peak
        # magnitude, so buffer the golden first to learn that scale. A reduction's
        # float32 reassociation error is set by the size of the terms summed, not
        # by the size of an individual result, so an element that happens to
        # cancel to near zero must not be held to a near-zero absolute tolerance.
        code_lines.append(f"            static float verif_golden[{total_out}];")
        code_lines.append("            long gn = 0;")
        code_lines.append(f"            for (int i = 0; i < {total_out}; i++) {{")
        code_lines.append("                float gv;")
        code_lines.append("                if (fscanf(gf, \"%f\", &gv) != 1) break;")
        code_lines.append("                verif_golden[i] = gv; gn++;")
        code_lines.append("            }")
        code_lines.append("            double verif_scale = 0.0;")
        code_lines.append("            for (long i = 0; i < gn; i++) {")
        code_lines.append("                double m = fabs((double)verif_golden[i]);")
        code_lines.append("                if (m > verif_scale) verif_scale = m;")
        code_lines.append("            }")
        code_lines.append("            double verif_atol = VERIF_ATOL + VERIF_ATOL_SCALE * verif_scale;")
        code_lines.append("            for (long i = 0; i < gn; i++) {")
        code_lines.append(f"                double a = (double)(float)((data_t*){out_name})[i];")
        code_lines.append("                double b = (double)verif_golden[i];")
        code_lines.append("                double abs_err = fabs(a - b);")
        code_lines.append("                double rel_err = abs_err / (fabs(b) + 1e-12);")
        code_lines.append("                double tol = verif_atol + VERIF_RTOL * fabs(b);")
        code_lines.append("                int bad = (!(abs_err <= tol)) || (!isfinite(a));")
        code_lines.append("                if (abs_err > verif_max_abs) verif_max_abs = abs_err;")
        code_lines.append("                if (rel_err > verif_max_rel) verif_max_rel = rel_err;")
        code_lines.append("                if (bad) verif_n_mismatch++;")
        code_lines.append("                verif_n_total++;")
        code_lines.append("            }")
        code_lines.append("            fclose(gf);")
        code_lines.append("            verif_n_checked++;")
        code_lines.append("        }")
        code_lines.append("    }")
        code_lines.append("")

    # Emit a machine-parseable verdict and return nonzero on failure.
    code_lines.append("    if (verif_n_checked == 0) {")
    code_lines.append("        printf(\"VERIFICATION: SKIP (no golden files found)\\n\");")
    code_lines.append("        return 0;")
    code_lines.append("    }")
    code_lines.append("    if (verif_n_mismatch == 0) {")
    code_lines.append("        printf(\"VERIFICATION: PASS (max_abs=%g, max_rel=%g, n=%ld)\\n\", verif_max_abs, verif_max_rel, verif_n_total);")
    code_lines.append("        return 0;")
    code_lines.append("    }")
    code_lines.append("    printf(\"VERIFICATION: FAIL (max_abs=%g, max_rel=%g, n_mismatch=%ld/%ld)\\n\", verif_max_abs, verif_max_rel, verif_n_mismatch, verif_n_total);")
    code_lines.append("    return 1;")
    code_lines.append("}")

    return "\n".join(code_lines)


def generate_dram_txt_files(drams, seed=None, low=0.0, high=1.0):
    """
    For each DRAM in the configuration, generate a .txt file containing random
    numbers in [low, high), one per line.

    Parameters:
      - drams: a list of dictionaries. Each dictionary should have:
           "name": string, e.g., "DRAM_1"
           "dims": list of integers, e.g., [2, 4, 4]
      - seed: optional integer seed for reproducibility.
      - low, high: input range. The default [0, 1) is the historical behavior, but
        it is strictly non-negative, so any op with a sign-dependent branch (relu,
        leaky_relu, elu, prelu, ...) never exercises its negative path and any op
        with a clamp (relu6 cap, thresholded_relu theta) never reaches it. Set a
        config's "input_range" to widen this for functional verification.
    """
    if seed is not None:
        random.seed(seed)

    for dram in drams:
        total_elements = prod(dram["dims"])
        filename = f"{dram['name']}.txt"
        # A DRAM may override the design-wide range when its contents are not
        # free-form data -- e.g. batchnorm's weights array holds a variance term
        # that must stay non-negative or sqrt() yields NaN.
        dram_low, dram_high = dram.get("input_range", (low, high))
        with open(filename, "w") as f:
            numbers = [str(random.uniform(dram_low, dram_high)) for _ in range(total_elements)]
            # Write each number on a new line.
            f.write("\n".join(numbers))
        print(f"Generated {filename} with {total_elements} random numbers.")

def generate_full_tcl_file(drams, FPGA_name, clock_period, task, output_filename="design.tcl"):
    """
    Generates a TCL file for HLS that includes the add_files -tb commands for each DRAM.
    
    Parameters:
      - drams: list of dictionaries, each with a "name" key (e.g., "DRAM_1")
      - output_filename: the name of the TCL file to generate.
      
    The generated TCL file will contain lines like:
        add_files -tb DRAM_1.txt
        add_files -tb DRAM_2.txt
        ...
    """
    # You can add a header if needed.
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

    # Generate add_files lines for each DRAM based on user configuration.
    for dram in drams:
        lines.append(f"add_files -tb {dram['name']}.txt")
    
    lines.append('open_solution "solution1"')
    lines.append("")
    lines.append(f"set_part {FPGA_name}")
    lines.append("")
    lines.append(f"create_clock -period {clock_period} -name default")
    lines.append("")
    
    if "csim" in task:
        lines.append("csim_design")
        lines.append("")
    if "csynth" in task:
        lines.append("csynth_design")
        lines.append("")
    if "cosim" in task:
        lines.append("cosim_design")
        lines.append("")
    if "export_ip" in task:
        lines.append("export_design -format ip_catalog -flow impl")
        lines.append("")
        
    lines.append("exit")
    # (Optional) Add other static TCL commands if needed.
    # For example:
    # lines.append("")
    # lines.append("open_project my_project")
    # lines.append("set_part {xc7z020clg484-1}")
    # etc.
    
    # Write the TCL file.
    with open(output_filename, "w") as f:
        f.write("\n".join(lines))
    
    print(f"Generated TCL file '{output_filename}' with the following contents:")
    print("\n".join(lines))



if __name__ == "__main__":
    # Define transformer block parameters.
    SEQ_LENGTH = 8
    DIM_IN     = 32
    NUM_HEAD   = 4
    DIM_Q      = DIM_IN / NUM_HEAD
    DIM_K      = DIM_IN / NUM_HEAD
    DIM_V      = DIM_IN / NUM_HEAD
    DIM_OUT    = 32

    brams = [
            {"name": "BRAM_attn_input",      "dims": [SEQ_LENGTH, DIM_IN]},
            {"name": "BRAM_weights_q",       "dims": [DIM_IN, DIM_IN]},
            {"name": "BRAM_weights_k",       "dims": [DIM_IN, DIM_IN]},
            {"name": "BRAM_weights_v",       "dims": [DIM_IN, DIM_IN]},
            {"name": "BRAM_1",     "dims": [SEQ_LENGTH, DIM_OUT]},
            {"name": "BRAM_2",     "dims": [SEQ_LENGTH, DIM_OUT]},
            {"name": "BRAM_MLP_1",     "dims": [SEQ_LENGTH, 4 * DIM_OUT]},
            {"name": "BRAM_MLP_2",     "dims": [SEQ_LENGTH, 4 * DIM_OUT]},
            {"name": "BRAM_layer_norm_weights_1",     "dims": [2, DIM_OUT]},
            {"name": "FF_weights_1",     "dims": [4 * DIM_OUT, DIM_OUT]},
            {"name": "FF_weights_2",     "dims": [DIM_OUT, 4 * DIM_OUT]},
            {"name": "BRAM_layer_norm_weights_2",     "dims": [2, DIM_OUT]},
            
        ]

        # Define DRAM configuration (for input/output).
    drams = [
        {"name": "DRAM_attn_input",  "dims": [SEQ_LENGTH, DIM_IN],  "bundle": "mem1"},
        {"name": "DRAM_weights_q",  "dims": [DIM_IN, DIM_IN],  "bundle": "mem1"},
        {"name": "DRAM_weights_k",  "dims": [DIM_IN, DIM_IN],  "bundle": "mem1"},
        {"name": "DRAM_weights_v",  "dims": [DIM_IN, DIM_IN],  "bundle": "mem1"},
        {"name": "DRAM_layer_norm_weights_1",  "dims": [2, DIM_OUT],  "bundle": "mem1"},
        {"name": "DRAM_FF_weights_1",  "dims": [4 * DIM_OUT, DIM_OUT],  "bundle": "mem1"},
        {"name": "DRAM_FF_weights_2",  "dims": [DIM_OUT, 4 * DIM_OUT],  "bundle": "mem1"},
        {"name": "DRAM_layer_norm_weights_2",  "dims": [2, DIM_OUT],  "bundle": "mem1"},
        {"name": "DRAM_output", "dims": [SEQ_LENGTH, DIM_OUT], "bundle": "mem2"}
    ]



    # Build the ops dictionary.
    ops = {
        "load_1": {
            "func_name": "load",
            "dims": [SEQ_LENGTH, DIM_IN],
            "args": ["DRAM_attn_input", "BRAM_attn_input"]
        },
        "load_2": {
            "func_name": "load",
            "dims": [DIM_IN, DIM_IN],
            "args": ["DRAM_weights_q", "BRAM_weights_q"]
        },
        "load_3": {
            "func_name": "load",
            "dims": [DIM_IN, DIM_IN],
            "args": ["DRAM_weights_k", "BRAM_weights_k"]
        },
        "load_4": {
            "func_name": "load",
            "dims": [DIM_IN, DIM_IN],
            "args": ["DRAM_weights_v", "BRAM_weights_v"]
        },
        "load_5": {
            "func_name": "load",
            "dims": [2, DIM_OUT],
            "args": ["DRAM_layer_norm_weights_1", "BRAM_layer_norm_weights_1"]
        },
        "load_6": {
            "func_name": "load",
            "dims": [4 * DIM_OUT, DIM_OUT],
            "args": ["DRAM_FF_weights_1", "FF_weights_1"]
        },
        "load_7": {
            "func_name": "load",
            "dims": [DIM_OUT, 4 * DIM_OUT],
            "args": ["DRAM_FF_weights_2", "FF_weights_2"]
        },
        "load_8": {
            "func_name": "load",
            "dims": [2, DIM_OUT],
            "args": ["DRAM_layer_norm_weights_2", "BRAM_layer_norm_weights_2"]
        },
        "mha": {
            "func_name": "mha",
            "dims": [SEQ_LENGTH, DIM_IN, NUM_HEAD, int(DIM_IN/NUM_HEAD)],
            "func_info": ["grouped_mha_rope_template.cpp", False],
            "args": ["BRAM_attn_input", "BRAM_weights_q", "BRAM_weights_k", "BRAM_weights_v", "BRAM_1", "8"]
        },
        "swa": {
            "func_name": "swa",
            "dims": [SEQ_LENGTH, DIM_IN, NUM_HEAD, int(DIM_IN/NUM_HEAD)],
            "func_info": ["sliding_window_attention_template.cpp", False],
            "args": ["BRAM_attn_input", "BRAM_weights_q", "BRAM_weights_k", "BRAM_weights_v", "BRAM_1", "8"]
        },
        "dropout": {
            "func_name": "dropout",
            "dims": [SEQ_LENGTH, DIM_OUT],
            "func_info": ["dropout_template.cpp"],
            "args": ["BRAM_1", "BRAM_2", "0.5", "47"]
        },
        "layernorm_1": {
            "func_name": "layernorm",
            "dims": [SEQ_LENGTH, DIM_OUT, 1e-2],
            "func_info": ["layer_norm_template.cpp"],
            "args": ["BRAM_2", "BRAM_layer_norm_weights_1[0]", "BRAM_layer_norm_weights_1[1]", "BRAM_1"]
        },
        "matmul_1": {
            "func_name": "matmul",
            "dims": [SEQ_LENGTH, DIM_OUT, 4 * DIM_OUT],
            "func_info": ["matmul_template.cpp", False],
            "args": ["BRAM_1", "FF_weights_1", "BRAM_MLP_1"]
        },
        "activation": {
                "func_name": "activation",
                "dims": [SEQ_LENGTH, 4 * DIM_OUT],
                "func_info":["activation_template.cpp", "gelu"],
                "args": ["BRAM_MLP_1", "BRAM_MLP_2"]
            },
        "matmul_2": {
            "func_name": "matmul",
            "dims": [SEQ_LENGTH, 4 * DIM_OUT, DIM_OUT],
            "func_info": ["matmul_template.cpp", False],
            "args": ["BRAM_MLP_2", "FF_weights_2", "BRAM_2"]
        },
        "dropout_2": {
            "func_name": "dropout",
            "dims": [SEQ_LENGTH, DIM_OUT],
            "func_info": ["dropout_template.cpp"],
            "args": ["BRAM_2", "BRAM_1", "0.5", "47"]
        },
        "layernorm_2": {
            "func_name": "layernorm",
            "dims": [SEQ_LENGTH, DIM_OUT, 1e-2],
            "func_info": ["layer_norm_template.cpp"],
            "args": ["BRAM_1", "BRAM_layer_norm_weights_2[0]", "BRAM_layer_norm_weights_2[1]", "BRAM_2"]
        },
        "matrix_add": {
            "func_name": "matrix_add",
            "dims": [SEQ_LENGTH, DIM_OUT, 1e-2],
            "func_info": ["matrix_add_template.cpp"],
            "args": ["BRAM_1", "BRAM_2", "BRAM_2"]
        },
        "store": {
            "func_name": "store",
            "dims": [SEQ_LENGTH, DIM_OUT],
            "args": ["BRAM_2", "DRAM_output"]
        }
    }

    output_dram_names = ["DRAM_output"]
        
    FPGA_name = "xczu9eg-ffvb1156-2-e"
    clock_period = 10
    task = ["csim", "csynth", "cosim", "export_ip"]
    #task = ["csynth"]
    # Generate the complete HLS C code for the top function.
    top_code = generate_top_function(brams, drams, ops, data_type="ap_fixed<16, 5>", top_func_name="top")

    # Write the generated code to a file, for example "top.cpp"
    output_filename = "top.cpp"
    with open(output_filename, "w") as f:
        f.write(top_code)
    print("Generated top.cpp:")    

    top_h_code = generate_top_h(drams, data_type="ap_fixed<16, 5>", top_func_name="top")
    with open("top.h", "w") as f:
        f.write(top_h_code)
    print("Generated top.h:")

    tb_code = generate_testbench_code(drams, output_dram_names, data_type="ap_fixed<16, 5>", top_func_name="top")
    with open("tb_top.cpp", "w") as f:
        f.write(tb_code)
    print("Generated tb_top.cpp:")

    generate_dram_txt_files(drams, seed=42)
    print("Generated dram initialization.")

    generate_full_tcl_file(drams, FPGA_name, clock_period, task, output_filename="run_hls.tcl")
    print("Generated tcl file to launch tasks.")




