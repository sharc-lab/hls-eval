import os
import random
import re
import sys

# This module is executed with the domain directory as cwd (see the
# `subprocess ... cwd=domain_dir` call in verification/prepare_designs.py), so the
# repo root has to go on sys.path before `backends` resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backends


def _backend():
    """The active tool backend. Defaults to Vitis; set by gen_configs.run_hls_flow."""
    return backends.current()


def replace_data_type(data_type: str) -> str:
    """Sanitize a C++ type into a function-name suffix, per the active backend."""
    return _backend().type_suffix(data_type)


def generate_load_function(
    dims,              # List of dimensions, e.g., [8, 16, 16]
    data_type="float", # Underlying data type
    func_prefix="load" # Function prefix (will be appended with dims and data_type)
):
    """
    Generates an HLS C function that copies an input array to an output array.
    The function is for arrays of dimensions given in the list 'dims'.
    
    The generated function will have a name of the form:
      <func_prefix>_<dim1>_<dim2>_..._<dimN>_data_t
    
    Parameters:
      dims: list of integers, e.g., [8, 16, 16]
      data_type: string, e.g., "float" (used in typedef and function signature)
      func_prefix: prefix for the function name (default "load")
    
    Returns:
      A string with the generated HLS C code.
    """
    # Construct the typedef and include lines
    code_lines = []
    
    
    #code_lines.append(f"typedef {data_type} data_t;\n")
    
    # Build array dimension string, e.g., "[8][16][16]"
    array_dims = "".join(f"[{d}]" for d in dims)
    
    # Construct the function name. E.g., load_8_16_16_data_t
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
    dims,              # List of dimensions, e.g., [8, 16, 16]
    data_type="float", # Underlying data type
    func_prefix="store" # Function prefix (will be appended with dims and data_type)
):
    """
    Generates an HLS C function that copies an input array to an output array.
    The function is for arrays of dimensions given in the list 'dims'.
    
    The generated function will have a name of the form:
      <func_prefix>_<dim1>_<dim2>_..._<dimN>_data_t
    
    Parameters:
      dims: list of integers, e.g., [8, 16, 16]
      data_type: string, e.g., "float" (used in typedef and function signature)
      func_prefix: prefix for the function name (default "load")
    
    Returns:
      A string with the generated HLS C code.
    """
    # Construct the typedef and include lines
    code_lines = []
    #code_lines.append(f"typedef {data_type} data_t;\n")
    
    # Build array dimension string, e.g., "[8][16][16]"
    array_dims = "".join(f"[{d}]" for d in dims)
    
    # Construct the function name. E.g., load_8_16_16_data_t
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

###### GEMM FUNCTIONS ######

"""
GEMM JSON FORM:
{
    "func_name": "gemm",
    "dims": [M, N, K],
    "func_info":[order, unroll, with_bias, inline],  
    "args": [input_A, input_B, bias, output] 
},

order is ['i', 'j', 'k'] or a permutation of it
unroll is [factor_i, factor_j, factor_k] each factor is an int 
with_bias is bool
inline is bool

"""

def generate_gemm_function(
        data_type="float",
        func_type="gemm",
        M=16, N=16, K=16,
        order=['i', 'j', 'k'],
        unroll=[1,1,1],
        with_bias=False,
):
    """
    Generate a C++ HLS GEMM function based on the specified parameters.
    
    Args:
        data_type (str): Data type to use (e.g., "float", "int", "data_t")
        func_type (str): Function name
        M (int): First matrix dimension
        N (int): Second matrix dimension
        K (int): Third matrix dimension
        order (list): Order of loops (permutation of 'i', 'j', 'k')
        unroll (list): Unrolling + Array Partition factors for each loop - always i,j,k
        with_bias (bool): Whether to include bias in the computation
        
    Returns:
        str: The generated C++ function as a string
    """
    # Validate order parameter
    if sorted(order) != sorted(['i', 'j', 'k']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j', 'k']")
    
    # Determine function name and signature based on whether bias is included
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_bias"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}][{N}],
    {data_type} input_B[{N}][{K}],
    {data_type} bias[{M}][{K}],
    {data_type} output[{M}][{K}]
)"""
        init_out = "output[i][k] = bias[i][k];"

    else:
        function_name = f"{func_type}_{''.join(order)}"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}][{N}],
    {data_type} input_B[{N}][{K}],
    {data_type} output[{M}][{K}]
)"""
        init_out = "output[i][k] = 0;"

    partitioning = ""
    for idx, v in enumerate(unroll):
        var = int(v)
        if var > 1:
            if idx == 0:
                partition_pragma = (_backend().array_partition("input_A", var, idx + 1)
                                    + _backend().array_partition("output", var, idx + 1))
                if with_bias:
                    partition_pragma += _backend().array_partition("bias", var, idx + 1)
            elif idx == 1:
                partition_pragma = (_backend().array_partition("input_B", var, idx)
                                    + _backend().array_partition("input_A", var, idx + 1))
            elif idx == 2:
                partition_pragma = (_backend().array_partition("input_B", var, idx)
                                    + _backend().array_partition("output", var, idx))
                if with_bias:
                    partition_pragma += _backend().array_partition("bias", var, idx)
            partitioning += partition_pragma


    computation = "output[i][k] += input_A[i][j] * input_B[j][k];"
    
    # Create the loop structure based on specified order
    bias_loop_starts = ""
    bias_loop_ends = ""

    loop_starts = ""
    loop_ends = ""
    
    loop_vars = {'i': M, 'j': N, 'k': K}
    unroll_factors = {'i': unroll[0], 'j': unroll[1], 'k': unroll[2]}

    for var in order:
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        loop_ends = "}\n" + loop_ends
    
    for var in order:
        if var == 'j':
            continue
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        bias_loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        bias_loop_ends = "}\n" + bias_loop_ends
    
    # Create the complete function
    function =  f"""//////////////////////////////////////////
// Begin: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
/*==== {function_name.upper()} FUNCTION START ====*/
{function_signature}

{{
{partitioning}
{bias_loop_starts}    {init_out}
{bias_loop_ends}

{loop_starts}    {computation}
{loop_ends}}}
/*==== {function_name.upper()} FUNCTION END ====*/
//////////////////////////////////////////
// END: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
"""
    ext_func_name = f"{function_name}_{M}_{N}_{K}"
    return function, ext_func_name

def call_gemm(
        func_type="gemm",
        M=16, N=16, K=16,
        order=['i', 'j', 'k'],
        unroll=[1,1,1],
        with_bias=False,
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    """
    Generate C code that calls the appropriate GEMM function.
    
    Args:
        func_type (str): Function name prefix
        M, N, K (int): Matrix dimensions
        order (list): Order of loops (permutation of 'i', 'j', 'k')
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_var (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output
        
    Returns:
        str: C code that calls the GEMM function
    """
    # Validate order parameter
    if sorted(order) != sorted(['i', 'j', 'k']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j', 'k']")
    
    # Determine function name based on parameters
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_bias"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {bias_var}, {output_var});"
    else:
        function_name = f"{func_type}_{''.join(order)}"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {output_var});"
    
    # Create the complete function call with appropriate comment
    result = f"""//////////////////////////////////////////
// Begin: Call to {function_name.upper()}
//////////////////////////////////////////
{call_code}
//////////////////////////////////////////
// End: Call to {function_name.upper()}
//////////////////////////////////////////
"""
    
    return result

def call_gemm_inline(
        func_type="gemm",
        M=16, N=16, K=16,
        order=['i', 'j', 'k'],
        unroll=[1,1,1],
        with_bias=False,
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    """
    Generate inline C code that implements GEMM functionality without a function call.
    
    Args:
        func_type (str): Used for naming in comments only
        M, N, K (int): Matrix dimensions
        order (list): Order of loops (permutation of 'i', 'j', 'k')
        unroll (list): Unrolling + Array Partition factors for each loop - must align with order
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_vaKr (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output
        
    Returns:
        str: Inline C code that implements the GEMM functionality
    """
    # Validate order parameter
    if sorted(order) != sorted(['i', 'j', 'k']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j', 'k']")
    
    # Determine function name (for comments only) and computation
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_bias"
        init_out = f"{output_var}[i][k] = {bias_var}[i][k];"
    else:
        function_name = f"{func_type}_{''.join(order)}"
        init_out = f"{output_var}[i][k] = 0;"
    
    computation = f"{output_var}[i][k] += {input_A_var}[i][j] * {input_B_var}[j][k];"
    
    partitioning = ""
    for idx, v in enumerate(unroll):
        var = int(v)
        if var > 1:
            if idx == 0:
                partition_pragma = (_backend().array_partition(input_A_var, var, idx + 1)
                                    + _backend().array_partition(output_var, var, idx + 1))
                if with_bias:
                    partition_pragma += _backend().array_partition(bias_var, var, idx + 1)
            elif idx == 1:
                partition_pragma = (_backend().array_partition(input_B_var, var, idx)
                                    + _backend().array_partition(input_A_var, var, idx + 1))
            elif idx == 2:
                partition_pragma = (_backend().array_partition(input_B_var, var, idx)
                                    + _backend().array_partition(output_var, var, idx))
                if with_bias:
                    partition_pragma += _backend().array_partition(bias_var, var, idx)
            partitioning += partition_pragma

    # Create the loop structure based on specified order
    bias_loop_starts = ""
    bias_loop_ends = ""

    loop_starts = ""
    loop_ends = ""
    
    loop_vars = {'i': M, 'j': N, 'k': K}
    unroll_factors = {'i': unroll[0], 'j': unroll[1], 'k': unroll[2]}

    for var in order:
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        loop_ends = "}\n" + loop_ends
    
    for var in order:
        if var == 'j':
            continue
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        bias_loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        bias_loop_ends = "}\n" + bias_loop_ends
    
    # Create the complete inline implementation
    inline_code =   f"""//////////////////////////////////////////
// Begin: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
{partitioning}
{bias_loop_starts}    {init_out}
{bias_loop_ends}

{loop_starts}    {computation}
{loop_ends}//////////////////////////////////////////
// End: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
"""
    
    return inline_code

####### MM-V FUNCTIONS #######

"""
MM-V JSON FORM:
{
    "func_name": "mmv",
    "dims": [M, N],
    "func_info":[order, unroll, with_bias, inline],  
    "args": [input_A, input_B, bias, output] 
},

order is ['i', 'j'] or a permutation of it
unroll is [factor_i, factor_j] each factor is an int corresponding
with_bias is bool
inline is bool

"""

def generate_mmv_function(
        data_type="int",
        func_type="mmv",
        M=16, N=16,
        order=['i', 'j',],
        unroll=[1,1],
        with_bias=False,
):
    """
    Generate a C++ HLS Matrix * Vector (MMV) function based on the specified parameters.
    
    Args:
        data_type (str): Data type to use (e.g., "float", "int", "data_t")
        func_type (str): Function name
        M (int): First matrix dimension
        N (int): Second matrix dimension
        order (list): Order of loops (permutation of 'i', 'j',) leading dim determines if output is row or column vector, i -> column, j -> row
        unroll (list): Unrolling + Array Partition factors for each loop - must align with order
        with_bias (bool): Whether to include bias in the computation
        
    Returns:
        str: The generated C++ function as a string
    """
    # Validate order parameter
    if sorted(order) != sorted(['i', 'j']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j']")
    

    # Determine function name and signature based on whether bias is included
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_bias"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}][{N}],
    {data_type} input_B[{N}],
    {data_type} bias[{M}],
    {data_type} output[{M}]
)"""
        init_out = "output[i] = bias[i];"

    else:
        function_name = f"{func_type}_{''.join(order)}"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}][{N}],
    {data_type} input_B[{N}],
    {data_type} output[{M}]
)"""
        init_out = "output[i] = 0;"
    
    
    partitioning = ""
    for idx, v in enumerate(unroll):
        var = int(v)
        if var > 1:
            if idx == 0:
                partition_pragma = (_backend().array_partition("input_A", var, idx + 1)
                                    + _backend().array_partition("output", var, idx + 1))
                if with_bias:
                    partition_pragma += _backend().array_partition("bias", var, idx + 1)
            elif idx == 1:
                partition_pragma = (_backend().array_partition("input_B", var, idx)
                                    + _backend().array_partition("input_A", var, idx + 1))
                
            partitioning += partition_pragma

    computation = "output[i] += input_A[i][j] * input_B[j];"
    
    bias_loop_starts = ""
    bias_loop_ends = ""

    # Create the loop structure based on specified order
    loop_starts = ""
    loop_ends = ""
    
    loop_vars = {'i': M, 'j': N}
    unroll_factors = {'i': unroll[0], 'j': unroll[1]}

    for var in order:
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        loop_ends = "}\n" + loop_ends
    
    for var in order:
        if var == 'j':
            continue
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        bias_loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        bias_loop_ends = "}\n" + bias_loop_ends


    # Create the complete function
    function =  f"""//////////////////////////////////////////
// Begin: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
/*==== {function_name.upper()} FUNCTION START ====*/
{function_signature}
{{
{partitioning}
{bias_loop_starts}    {init_out}
{bias_loop_ends}

{loop_starts}    {computation}
{loop_ends}}}
/*==== {function_name.upper()} FUNCTION END ====*/
//////////////////////////////////////////
// END: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
"""
    ext_func_name = f"{function_name}_{M}_{N}"
    return function, ext_func_name

def call_mmv(
        func_type="mmv",
        M=16, N=16,
        order=['i', 'j',],
        unroll=[1,1],
        with_bias=False,  
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    """
    Generate C code that calls the appropriate Matrix * Vector (MMV) function.
    
    Args:
        data_type (str): Data type to use
        func_type (str): Function name prefix
        M, N (int): Matrix dimensions
        order (list): Order of loops (permutation of 'i', 'j',)
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_var (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output
        
    Returns:
        str: C code that calls the MMV function
    """
    # Validate order parameter
    if sorted(order) != sorted(['i', 'j']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j']")
    
    # Determine function name based on parameters
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_bias"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {bias_var}, {output_var});"
    else:
        function_name = f"{func_type}_{''.join(order)}"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {output_var});"
    
    # Create the complete function call with appropriate comment
    result = f"""//////////////////////////////////////////
    // Begin: Call to {function_name.upper()}
//////////////////////////////////////////
{call_code}
//////////////////////////////////////////
// End: Call to {function_name.upper()}
//////////////////////////////////////////
"""
    
    return result

def call_mmv_inline(
        func_type="mmv",
        M=16, N=16,
        order=['i', 'j',],
        unroll=[1,1],
        with_bias=False,  
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    """
    Generate inline C code that implements Matrix * Vector (MMV) functionality without a function call.

    Args:
        func_type (str): Function name prefix
        M, N (int): Matrix dimensions
        order (list): Order of loops (permutation of 'i', 'j',)
        unroll (list): Unrolling + Array Partition factors for each loop - must align with order
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_var (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output
        
    Returns:
        str: Inline C code that implements the MMV functionality
    """

    if sorted(order) != sorted(['i', 'j']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j']")
    
        
    # Determine function name (for comments only) and computation
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_bias"
        init_out = f"{output_var}[i] = {bias_var}[i];"
    else:
        function_name = f"{func_type}_{''.join(order)}"
        init_out = f"{output_var}[i] = 0;"
    
    partitioning = ""
    for idx, v in enumerate(unroll):
        var = int(v)
        if var > 1:
            if idx == 0:
                partition_pragma = (_backend().array_partition(input_A_var, var, idx + 1)
                                    + _backend().array_partition(output_var, var, idx + 1))
                if with_bias:
                    partition_pragma += _backend().array_partition(bias_var, var, idx + 1)
            elif idx == 1:
                partition_pragma = (_backend().array_partition(input_B_var, var, idx)
                                    + _backend().array_partition(input_A_var, var, idx + 1))
            partitioning += partition_pragma
            
    computation = f"{output_var}[i] += {input_A_var}[i][j] * {input_B_var}[j];"
    
    bias_loop_starts = ""
    bias_loop_ends = ""

    loop_starts = ""
    loop_ends = ""
    
    loop_vars = {'i': M, 'j': N}
    unroll_factors = {'i': unroll[0], 'j': unroll[1]}

    for var in order:
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        loop_ends = "}\n" + loop_ends
    
    for var in order:
        if var == 'j':
            continue
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        bias_loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        bias_loop_ends = "}\n" + bias_loop_ends

    # Create the complete inline implementation
    inline_code =   f"""//////////////////////////////////////////
// Begin: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
{partitioning}
{bias_loop_starts}    {init_out}
{bias_loop_ends}

{loop_starts}    {computation}
{loop_ends}//////////////////////////////////////////
// End: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
"""
    
    return inline_code

####### V-MM FUNCTIONS #######

"""
V-MM JSON FORM:
{
    "func_name": "vmm",
    "dims": [M, N],
    "func_info":[order, unroll, with_bias, inline],  
    "args": [input_A, input_B, bias, output] 
},

order is ['i', 'j'] or a permutation of it,
unroll is [factor_i, factor_j] each factor is an int corresponding to the loop of the same index in order 
with_bias is bool
inline is bool

"""

def generate_vmm_function(
        data_type="int",
        func_type="vmm",
        M=16, N=16,
        order=['i', 'j',],
        unroll=[1,1],
        with_bias=False,
):
    """
    Generate a C++ HLS Vector * Matrix (VMM) function based on the specified parameters.
    
    Args:
        data_type (str): Data type to use (e.g., "float", "int", "data_t")
        func_type (str): Function name
        M (int): First matrix dimension
        N (int): Second matrix dimension
        order (list): Order of loops (permutation of 'i', 'j',) 
        with_bias (bool): Whether to include bias in the computation
        
    Returns:
        str: The generated C++ function as a string
    """
    # Validate order parameter
    if sorted(order) != sorted(['i', 'j']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j']")
    

    # Determine function name and signature based on whether bias is included.
    # The dims are part of the function name (not just the dedup key): array
    # parameters decay to pointers, so two vmm ops that differ only in the outer
    # dim (e.g. [K][N] vs [M][K] with N==K) would otherwise emit two identically
    # -signed `vmm_ij` definitions -> "redefinition" (hits option_1 when K==N and
    # option_4 when N==K). Encoding M,N keeps every distinct shape a distinct name.
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_{M}_{N}_bias"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}][{N}],
    {data_type} input_B[{M}],
    {data_type} bias[{N}],
    {data_type} output[{N}]
)"""
        init_out = "output[j] = bias[j];"
    else:
        function_name = f"{func_type}_{''.join(order)}_{M}_{N}"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}][{N}],
    {data_type} input_B[{M}],
    {data_type} output[{N}]
)"""
        init_out = "output[j] = 0;"

    partitioning = ""
    for idx, v in enumerate(unroll):
        var = int(v)
        if var > 1:
            if idx == 0:
                partition_pragma = (_backend().array_partition("input_B", var, idx+1)
                                    + _backend().array_partition("input_A", var, idx + 1))
            elif idx == 1:
                partition_pragma = (_backend().array_partition("input_A", var, idx + 1)
                                    + _backend().array_partition("output", var, idx))
                if with_bias:
                    partition_pragma += _backend().array_partition("bias", var, idx)
                
            partitioning += partition_pragma


    computation = "output[j] += input_A[i][j] * input_B[i];"

    
    # Create the loop structure based on specified order
    bias_loop_starts = ""
    bias_loop_ends = ""

    loop_starts = ""
    loop_ends = ""
    
    loop_vars = {'i': M, 'j': N,}
    unroll_factors = {'i': unroll[0], 'j': unroll[1]}

    for var in order:
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        loop_ends = "}\n" + loop_ends
    
    for var in order:
        if var == 'i':
            continue
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        bias_loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        bias_loop_ends = "}\n" + bias_loop_ends
    
    # Create the complete function
    function =  f"""//////////////////////////////////////////
// Begin: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
/*==== {function_name.upper()} FUNCTION START ====*/
{function_signature}
{{
{partitioning}
{bias_loop_starts}    {init_out}
{bias_loop_ends}

{loop_starts}    {computation}
{loop_ends}}}
/*==== {function_name.upper()} FUNCTION END ====*/
//////////////////////////////////////////
// END: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
"""
    
    ext_func_name = function_name  # already unique per (order, M, N, bias)
    return function, ext_func_name

def call_vmm(
        data_type="int",
        func_type="vmm",
        M=16, N=16,
        order=['i', 'j',],
        unroll=[1,1],
        with_bias=False,  
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    """
    Generate C code that calls the appropriate Vector * Matrix (VMM) function.
    
    Args:
        data_type (str): Data type to use
        func_type (str): Function name prefix
        M, N (int): Matrix dimensions
        order (list): Order of loops (permutation of 'i', 'j',)
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_var (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output
        
    Returns:
        str: C code that calls the VMM function
    """
    # Validate order parameter
    if sorted(order) != sorted(['i', 'j']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j']")

    # Determine function name based on parameters. Must match the dims-encoded
    # definition name in generate_vmm_function (see note there).
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_{M}_{N}_bias"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {bias_var}, {output_var});"
    else:
        function_name = f"{func_type}_{''.join(order)}_{M}_{N}"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {output_var});"
    
    # Create the complete function call with appropriate comment
    result = f"""//////////////////////////////////////////
    // Begin: Call to {function_name.upper()}
//////////////////////////////////////////
{call_code}
//////////////////////////////////////////
// End: Call to {function_name.upper()}
//////////////////////////////////////////
"""
    
    return result

def call_vmm_inline(
        func_type="vmm",
        M=16, N=16,
        order=['i', 'j',],
        unroll=[1,1],
        with_bias=False,  
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    
    """
    Generate inline C code that implements Vector * Matrix (VMM) functionality without a function call.
    
    Args:
        func_type (str): Function name prefix
        M, N (int): Matrix dimensions
        order (list): Order of loops (permutation of 'i', 'j',)
        unroll (list): Unrolling + Array Partition factors for each loop - must align with order
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_var (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output
        
    Returns:
        str: Inline C code that implements the VMM functionality
    """
        
    if sorted(order) != sorted(['i', 'j']):
        raise ValueError("The 'order' parameter must be a permutation of ['i', 'j']")
    
        
    # Determine function name (for comments only) and computation
    if with_bias:
        function_name = f"{func_type}_{''.join(order)}_bias"
        init_out = f"{output_var}[j] = {bias_var}[j];"
    else:
        function_name = f"{func_type}_{''.join(order)}"
        init_out = f"{output_var}[j] = 0;"

    partitioning = ""
    for idx, v in enumerate(unroll):
        var = int(v)
        if var > 1:
            if idx == 0:
                partition_pragma = (_backend().array_partition(input_B_var, var, idx+1)
                                    + _backend().array_partition(input_A_var, var, idx + 1))
            elif idx == 1:
                partition_pragma = (_backend().array_partition(input_A_var, var, idx + 1)
                                    + _backend().array_partition(output_var, var, idx))
                if with_bias:
                    partition_pragma += _backend().array_partition(bias_var, var, idx)
                
            partitioning += partition_pragma

    computation = f"{output_var}[j] += {input_A_var}[i][j] * {input_B_var}[i];"

    bias_loop_starts = ""
    bias_loop_ends = ""

    loop_starts = ""
    loop_ends = ""
    
    loop_vars = {'i': M, 'j': N,}
    unroll_factors = {'i': unroll[0], 'j': unroll[1]}

    for var in order:
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        loop_ends = "}\n" + loop_ends
    
    for var in order:
        if var == 'i':
            continue
        limit = loop_vars[var]
        unroll_factor = unroll_factors[var]
        bias_loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {limit}; {var}++)", unroll_factor)
        bias_loop_ends = "}\n" + bias_loop_ends
        
    # Create the complete inline implementation
    inline_code =   f"""//////////////////////////////////////////
// Begin: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
{partitioning}
{bias_loop_starts}    {init_out}
{bias_loop_ends}

{loop_starts}    {computation}
{loop_ends}//////////////////////////////////////////
// End: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
"""
    
    return inline_code

####### DOT PRODUCT FUNCTIONS #######

"""
DOT PRODUCT JSON FORM:
{
    "func_name": "dot_product",
    "dims": [M],
    "func_info":[unroll, with_bias, inline],  
    "args": [input_A, input_B, bias, output] 
},

unroll is int
with_bias is bool
inline is bool

"""

def generate_dot_function(
        data_type="int",
        func_type="dot_product",
        M=16,
        unroll=1,
        with_bias=False,
):
    """
    Generate a C++ HLS Dot Product function based on the specified parameters.
    
    Args:
        data_type (str): Data type to use (e.g., "float", "int", "data_t")
        func_type (str): Function name
        unroll (int): Unrolling + Array Partition factors
        M (int): Vector dimension
        with_bias (bool): Whether to include bias in the computation
        
    Returns:
        str: The generated C++ function as a string
    """
    # Determine function name and signature based on whether bias is included
    if with_bias:
        function_name = f"{func_type}_bias"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}],
    {data_type} input_B[{M}],
    {data_type} bias[1],
    {data_type} output[1]
)"""
        init_out = "output[0] = bias[0];"

    else:
        function_name = f"{func_type}"
        function_signature =    f"""void {function_name}(
    {data_type} input_A[{M}],
    {data_type} input_B[{M}],
    {data_type} output[1]
)"""
        init_out = "output[0] = 0;"
    
    partitioning = ""
    unroll = int(unroll)
    if unroll > 1:
        partitioning = _backend().array_partition("input_A", unroll, 1)
        partitioning += _backend().array_partition("input_B", unroll, 1)

    computation = "output[0] += input_A[i] * input_B[i];"
    
    # Create the loop structure based on specified order


    loop_starts = ""
    loop_ends = ""
    
    for var in ['i']:
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {M}; {var}++)", unroll)
        loop_ends = "}\n" + loop_ends
    
    # Create the complete function
    function =  f"""//////////////////////////////////////////
// Begin: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
/*==== {function_name.upper()} FUNCTION START ====*/
{function_signature}
{{
{partitioning}
{init_out}

{loop_starts}    {computation}
{loop_ends}}}
/*==== {function_name.upper()} FUNCTION END ====*/
//////////////////////////////////////////
// END: {function_name.upper()} FUNCTION{' with BIAS' if with_bias else ''}
//////////////////////////////////////////
"""
    
    return function, function_name

def call_dot(
        func_type="dot_product",
        M=16,
        unroll=1,
        with_bias=False,  
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    """
    Generate C code that calls the appropriate Dot Product function.

    Args:
        func_type (str): Function name
        M (int): Vector dimension
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_var (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output

    Returns:
        str: C code that calls the Dot Product function
    """
    
    # Determine function name based on parameters
    if with_bias:
        function_name = f"{func_type}_bias"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {bias_var}, {output_var});"
    else:
        function_name = f"{func_type}"
        call_code = f"{function_name}({input_A_var}, {input_B_var}, {output_var});"
    
    # Create the complete function call with appropriate comment
    result = f"""//////////////////////////////////////////
    // Begin: Call to {function_name.upper()}
//////////////////////////////////////////
{call_code}
//////////////////////////////////////////
// End: Call to {function_name.upper()}
//////////////////////////////////////////
"""
    
    return result

def call_dot_inline(
        func_type="dot_product",
        M=16,
        unroll=1,
        with_bias=False,  
        input_A_var="input_A",
        input_B_var="input_B",
        bias_var="bias",
        output_var="output"
):
    """
    Generate inline C code that implements Dot Product functionality without a function call.

    Args:
        func_type (str): Function name
        M (int): Vector dimension
        unroll (int): Unrolling + Array Partition factor
        with_bias (bool): Whether to include bias in the computation
        input_A_var (str): Variable name for input A
        input_B_var (str): Variable name for input B
        bias_var (str): Variable name for bias
        output_var (str): Variable name for output

    Returns:
        str: Inline C code that implements the Dot Product functionality
    """

    # Determine function name (for comments only) and computation
    if with_bias:
        function_name = f"{func_type}_bias"
        init_out = f"{output_var}[0] = {bias_var}[0];"
    else:
        function_name = f"{func_type}"
        init_out = f"{output_var}[0] = 0;"

    partitioning = ""
    unroll = int(unroll)
    if unroll > 1:
        partitioning = _backend().array_partition(input_A_var, unroll, 1)
        partitioning += _backend().array_partition(input_B_var, unroll, 1)

    computation = f"{output_var}[0] += {input_A_var}[i] * {input_B_var}[i];"
    
    loop_starts = ""
    loop_ends = ""
    
    for var in ['i']:
        loop_starts += _backend().open_loop(f"for (int {var} = 0; {var} < {M}; {var}++)", unroll)
        loop_ends = "}\n" + loop_ends
    
    # Create the complete inline implementation
    inline_code =   f"""//////////////////////////////////////////
// Begin: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
{partitioning}
{init_out}

{loop_starts}    {computation}
{loop_ends}//////////////////////////////////////////
// End: Inline implementation of {function_name.upper()}
//////////////////////////////////////////
"""
    
    return inline_code

####### 2D ACTIVATION FUNCTIONS #######

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


def activation_extra_args(func_info):
    """Literal call arguments for an activation's extra scalar parameters."""
    name = func_info[1].lower()
    if name == "tanh":
        name = "tanh_act"
    values = list(func_info[2:]) or ACTIVATION_EXTRA_PARAMS.get(name, [])
    return [f"(data_t){float(v)!r}" for v in values]


def generate_activation_function(
    template_path,      # Path to activations_template.cpp
    func_name,          # One of: "relu", "leaky_relu", "prelu", "rrelu", "thresholded_relu", "relu6", "sigmoid", "tanh_act", "elu", "selu", "gelu", "swish", "softmax"
    DATA_TYPE="float",
    H=64,
    W=64
):
    """
    Reads an external activation functions template, substitutes common placeholders,
    extracts the specified function block (for a 3D tensor with dimensions [C][H][W]),
    appends the dimension information to the function name, and writes the final HLS C code to output_path.
    
    Expected placeholders in the template:
      {DATA_TYPE}, {H}, {W}
    """
    # 1) Read the full template file.
    with open(template_path, "r") as f:
        template_code = f.read()
    
    # 2) Substitute common placeholders.
    formatted_code = template_code.format(
        DATA_TYPE=DATA_TYPE,
        H=H,
        W=W
    )
    
    # 3) Set marker strings based on the requested function name.
    func_name = func_name.lower()  # make case-insensitive
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
        raise ValueError("Invalid function name. Choose from: relu, leaky_relu, prelu, rrelu, thresholded_relu, relu6, sigmoid, tanh_act, elu, selu, gelu, swish, softmax.")
    
    # 4) Extract the function block.
    start_idx = formatted_code.find(marker_start)
    end_idx = formatted_code.find(marker_end)
    if start_idx == -1 or end_idx == -1:
        raise ValueError("Could not find the specified function markers in the template.")
    
    # Skip the marker text.
    function_block = formatted_code[start_idx + len(marker_start): end_idx].strip()
    
    # 5) Append dimension information to the function name.
    # We'll assume the function signature starts with "void <name>(".
    DATA_TYPE = replace_data_type(DATA_TYPE)
    dim_suffix = f"_{H}_{W}_{DATA_TYPE}"
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

    # 6) Optionally, include a header (everything before the first marker).
    header_end = formatted_code.find("/*====")
    if header_end != -1:
        header = formatted_code[:header_end].strip() + "\n\n"
    else:
        header = ""

    output_code = header + function_block

    emitted_name = captured_name[0] if captured_name else func_name
    return output_code, emitted_name + dim_suffix

def generate_func_def(op_info, data_type):
    
    if op_info['func_name'] == 'load':
        code_line, full_func_name = generate_load_function(op_info["dims"], data_type, func_prefix="load")
    elif op_info['func_name'] == 'store':
        code_line, full_func_name = generate_store_function(op_info["dims"], data_type, func_prefix="store")
    elif op_info['func_name'] == 'gemm':
        code_line, full_func_name = generate_gemm_function(data_type, "gemm", op_info["dims"][0], op_info["dims"][1], op_info["dims"][2], op_info["func_info"][0], op_info["func_info"][1], op_info["func_info"][2])
    elif op_info['func_name'] == 'vmm':
        code_line, full_func_name = generate_vmm_function(data_type, "vmm", op_info["dims"][0], op_info["dims"][1], op_info["func_info"][0], op_info["func_info"][1], op_info["func_info"][2])
    elif op_info['func_name'] == 'mmv':
        code_line, full_func_name = generate_mmv_function(data_type, "mmv", op_info["dims"][0], op_info["dims"][1], op_info["func_info"][0], op_info["func_info"][1], op_info["func_info"][2])
    elif op_info['func_name'] == 'dot_product':
        code_line, full_func_name = generate_dot_function(data_type, "dot_product", op_info["dims"][0], op_info["func_info"][0], op_info["func_info"][1])
    elif op_info['func_name'] == 'activation':
        code_line, full_func_name = generate_activation_function(op_info["func_info"][0], op_info["func_info"][1], data_type,  op_info["dims"][0], op_info["dims"][1])
    else:
        print("the operator we do not support!")
        
    return code_line, full_func_name

def generate_operator_call(op_info, data_type):
    """
    Generates a single function call string given an operator dictionary.
    
    op_info: dict with keys:
       - "func_name": base function name (e.g., "load", "conv2d", etc.)
       - "dims": list of integers (e.g., [8,16,16] or [8,16,16,8,16,16])
       - "args": list of argument strings for the function call
       
    Returns a string like:
       load_8_16_16_data_t(DRAM_1, BRAM_1);
    """

    # Append _data_t to follow the convention.
    if op_info['func_name'] == 'load':
        code_line, full_func_name = generate_load_function(op_info["dims"], data_type, func_prefix="load")
        args_str = ", ".join(op_info["args"])
        call_str =  f"{full_func_name}({args_str});"
    elif op_info['func_name'] == 'store':
        code_line, full_func_name = generate_store_function(op_info["dims"], data_type, func_prefix="store")
        args_str = ", ".join(op_info["args"])
        call_str =  f"{full_func_name}({args_str});"
    elif op_info['func_name'] == 'activation':
        code_line, full_func_name = generate_activation_function(op_info["func_info"][0], op_info["func_info"][1], data_type,  op_info["dims"][0], op_info["dims"][1])
        args_str = ", ".join(list(op_info["args"]) + activation_extra_args(op_info["func_info"]))
        call_str =  f"{full_func_name}({args_str});"
    elif op_info['func_name'] == 'gemm':
        if op_info["func_info"][-1]: # inline
            call_str = call_gemm_inline(func_type="gemm", M=op_info["dims"][0], N=op_info["dims"][1], K=op_info["dims"][2], 
                        order=op_info["func_info"][0], unroll=op_info["func_info"][1], with_bias=op_info["func_info"][2], 
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
        else:
            call_str = call_gemm(func_type="gemm", M=op_info["dims"][0], N=op_info["dims"][1], K=op_info["dims"][2], 
                        order=op_info["func_info"][0], unroll=op_info["func_info"][1], with_bias=op_info["func_info"][2], 
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
    elif op_info['func_name'] == 'vmm':
        if op_info["func_info"][-1]:
            call_str = call_vmm_inline(func_type="vmm", M=op_info["dims"][0], N=op_info["dims"][1], 
                        order=op_info["func_info"][0], unroll=op_info["func_info"][1], with_bias=op_info["func_info"][2], 
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
        else:
            call_str = call_vmm(func_type="vmm", M=op_info["dims"][0], N=op_info["dims"][1], 
                        order=op_info["func_info"][0], unroll=op_info["func_info"][1], with_bias=op_info["func_info"][2], 
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
    elif op_info['func_name'] == 'mmv':
        if op_info["func_info"][-1]:
            call_str = call_mmv_inline(func_type="mmv", M=op_info["dims"][0], N=op_info["dims"][1], 
                        order=op_info["func_info"][0], unroll=op_info["func_info"][1], with_bias=op_info["func_info"][2], 
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
        else:
            call_str = call_mmv(func_type="mmv", M=op_info["dims"][0], N=op_info["dims"][1], 
                        order=op_info["func_info"][0], unroll=op_info["func_info"][1], with_bias=op_info["func_info"][2], 
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
    elif op_info['func_name'] == 'dot_product':
        if op_info["func_info"][-1]:
            call_str = call_dot_inline(func_type="dot_product", M=op_info["dims"][0], 
                        unroll=op_info["func_info"][0], with_bias=op_info["func_info"][1],
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
        else:
            call_str = call_dot(func_type="dot_product", M=op_info["dims"][0], 
                        unroll=op_info["func_info"][0], with_bias=op_info["func_info"][1], 
                        input_A_var=op_info["args"][0], input_B_var=op_info["args"][1], bias_var=op_info["args"][2], output_var=op_info["args"][3])
    else:
        print("the operator we do not support!")

    return call_str

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
    backend = _backend()
    ctype = backend.type_decl(data_type)

    # The op bodies and the inlined calls are generated FIRST, before anything is
    # emitted, because generating them is what tells the backend which arrays want
    # partitioning. Catapult's `hls_interleave` attaches to the array declaration,
    # so the BRAM declarations below cannot be written until those requests are in.
    # Buffering here does not change the Vitis output: the pieces are still
    # assembled in the original order.
    func_def_lines = []
    func_name_set = set()
    func_def_name_list = []

    for key, op_info in ops.items():
       func_def_code, func_name  = generate_func_def(op_info, ctype)
       if func_name not in func_name_set:
           func_name_set.add(func_name)
           func_def_lines.append(func_def_code)
           func_def_lines.append("")
           func_def_name_list.append(func_name)

    call_lines = []
    # If ops is a dictionary, we iterate in insertion order.
    for key, op_info in ops.items():
        call_str = generate_operator_call(op_info, ctype)
        call_lines.append(f"    {call_str}")

    code_lines = []

    code_lines.append("")
    code_lines.extend(backend.includes_top_cpp())
    code_lines.append(f"using namespace std;\n")

    # 1. Write typedef.
    code_lines.append(f"typedef {ctype} data_t;\n")

    # 2. Declare BRAM arrays, carrying any partitioning the backend wants placed
    #    on the declaration rather than at the use site.
    decl_pragma = getattr(backend, "declaration_pragmas", None)
    for bram in brams:
        dims_str = "".join(f"[{d}]" for d in bram["dims"])
        if decl_pragma:
            code_lines.append(
                decl_pragma(bram["name"], bram["dims"]) + f"data_t {bram['name']}{dims_str};"
            )
        else:
            code_lines.append(f"data_t {bram['name']}{dims_str};")

    code_lines.append("")  # blank line

    code_lines.extend(func_def_lines)

    # 3. Build the top function signature with DRAM parameters.
    dram_params = []
    for dram in drams:
        dims_str = "".join(f"[{d}]" for d in dram["dims"])
        dram_params.append(f"data_t {dram['name']}{dims_str}")
    params_str = ", ".join(dram_params)
    code_lines.append(f"void {top_func_name}({params_str})")
    code_lines.append("{")

    # 4. Insert the top-level interface pragmas (Vitis m_axi; none for Catapult).
    code_lines.extend(backend.interface(drams))

    code_lines.append("")  # blank line before function calls

    # 5. Emit the operator function calls generated above.
    code_lines.extend(call_lines)

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
    lines.extend(_backend().includes_top_h())
    lines.append("#ifndef TOP_H")
    lines.append("#define TOP_H")
    lines.append("")
    lines.append(f"typedef {_backend().type_decl(data_type)} data_t;")
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
    code_lines.extend(_backend().includes_tb())
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
    Generates the tool build script for this design.

    Which script gets written -- Vitis `run_hls.tcl` or a Catapult project script --
    is decided by the active backend; `FPGA_name` carries the Vitis part for the
    Vitis backend and the target library list for Catapult.

    Parameters:
      - drams: list of dictionaries, each with a "name" key (e.g., "DRAM_1")
      - output_filename: the name of the TCL file to generate.
    """
    _backend().emit_script(drams, FPGA_name, clock_period, task, output_filename)

