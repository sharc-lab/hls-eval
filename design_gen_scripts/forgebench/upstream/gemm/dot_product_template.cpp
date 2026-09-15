/*
 * Auto-generated GEMM/VMM/DOT HLS Code (with optional bias and grouping)

// Use a typedef for the data type

//////////////////////////////////////////
// Begin: GEMM FUNCTION with BIAS
//////////////////////////////////////////
/*==== GEMM BIAS FUNCTION START ====*/
void gemm_bias(
    data_t input_A[{M}][{N}],
    data_t input_B[{N}][{K}],
    data_t bias[{M}][{K}],
    data_t output[{M}][{K}]
)
{{
    for (int i = 0; i < {M}; i++) {{
        for (int j = 0; j < {N}; j++) {{
            for (int k = 0; k < {K}; k++) {{
                output[i][j] += input_A[i][j] * input_B[j][k] + bias[i][k];
            }}
        }}
    }}
}}
/*==== GEMM BIAS FUNCTION END ====*/
//////////////////////////////////////////
// END: GEMM FUNCTION with BIAS 
//////////////////////////////////////////

//////////////////////////////////////////
// Begin: GEMM FUNCTION 
//////////////////////////////////////////
/*==== GEMM FUNCTION START ====*/
void gemm(
    data_t input_A[{M}][{N}],
    data_t input_B[{N}][{K}],
    data_t output[{M}][{K}]
)
{{
    for (int i = 0; i < {M}; i++) {{
        for (int j = 0; j < {N}; j++) {{
            for (int k = 0; k < {K}; k++) {{
                output[i][j] += input_A[i][j] * input_B[j][k];
            }}
        }}
    }}
}}   
/*==== GEMM FUNCTION END ====*/
//////////////////////////////////////////
// END: GEMM FUNCTION 
//////////////////////////////////////////

//////////////////////////////////////////
// Vector-Matrix Multiplication (VMM) FUNCTION with BIAS 
//////////////////////////////////////////
/*==== VMM BIAS FUNCTION START ====*/
void vmm_bias(
    data_t input_A[{M}][{N}],
    data_t input_B[{N}],
    data_t bias[{M}],
    data_t output[{M}]
)
{{
    for (int i = 0; i < {M}; i++) {{
        for (int j = 0; j < {N}; j++) {{
            output[i] += input_A[i][j] * input_B[j] + bias[i];
        }}
    }}
}}   
/*==== VMM BIAS FUNCTION END ====*/
//////////////////////////////////////////
// END: Vector-Matrix Multiplication (VMM) FUNCTION with BIAS 
//////////////////////////////////////////

//////////////////////////////////////////
// Begin: Vector-Matrix Multiplication (VMM) FUNCTION 
//////////////////////////////////////////
/*==== VMM FUNCTION START ====*/
void vmm(
    data_t input_A[{M}][{N}],
    data_t input_B[{N}],
    data_t output[{M}]
)
{{
    for (int i = 0; i < {M}; i++) {{
        for (int j = 0; j < {N}; j++) {{
            output[i] += input_A[i][j] * input_B[j];
        }}
    }}
}}
/*==== VMM FUNCTION END ====*/
//////////////////////////////////////////
// END: Vector-Matrix Multiplication (VMM) FUNCTION
//////////////////////////////////////////

//////////////////////////////////////////
// Begin: DOT PRODUCT FUNCTION with BIAS
//////////////////////////////////////////
/*==== DOT BIAS FUNCTION START ====*/
void dot_product_bias(
    data_t input_A[{M}],
    data_t input_B[{M}],
    data_t bias,
    data_t output[1]
)
{{
    for (int i = 0; i < {M}; i++) {{
        output[0] += input_A[i] * input_B[i] + bias;
    }}
}}
/*==== DOT BIAS FUNCTION END ====*/
//////////////////////////////////////////
// END: DOT PRODUCT FUNCTION with BIAS
//////////////////////////////////////////

//////////////////////////////////////////
// Begin: DOT PRODUCT FUNCTION
//////////////////////////////////////////
/*==== DOT FUNCTION START ====*/
void dot_product(
    data_t input_A[{M}],
    data_t input_B[{M}],
    data_t output[1]
)
{{
    for (int i = 0; i < {M}; i++) {{
        output[0] += input_A[i] * input_B[i];
    }}
}}

