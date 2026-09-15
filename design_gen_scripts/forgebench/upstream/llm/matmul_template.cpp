

void matmul(
    data_t input[{SEQ_LENGTH}][{DIM_IN}],
    data_t weights[{DIM_OUT}][{DIM_IN}],
{BIAS_ARG}    data_t output[{SEQ_LENGTH}][{DIM_OUT}]
)
{{
    // Initialize output to {INIT_VAL}
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        for (int j = 0; j < {DIM_OUT}; j++) {{
            output[i][j] = {INIT_VAL};
        }}
    }}

    // Matrix multiplication
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        for (int k = 0; k < {DIM_IN}; k++) {{
            for (int j = 0; j < {DIM_OUT}; j++) {{
                output[i][j] += input[i][k] * weights[j][k];
            }}
        }}
    }}
}}
