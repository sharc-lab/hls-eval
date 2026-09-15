
void elementwise_mult(
    data_t in1[{SEQ_LENGTH}][{DIM}],
    data_t in2[{SEQ_LENGTH}][{DIM}],
    data_t out[{SEQ_LENGTH}][{DIM}]
)
{{
    
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        for (int j = 0; j < {DIM}; j++) {{
            out[i][j] = in1[i][j] * in2[i][j];
        }}
    }}
    
}}





