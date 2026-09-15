
void rms_norm(
    data_t input[{SEQ_LENGTH}][{DIM}],
    data_t gamma[{DIM}],
    data_t output[{SEQ_LENGTH}][{DIM}]
)
{{
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        data_t sum_sq = (data_t)0;
        for (int j = 0; j < {DIM}; j++) {{
            sum_sq += input[i][j] * input[i][j];
        }}
        data_t rms = hls::sqrt(sum_sq / (data_t){DIM} + (data_t){EPSILON});
        for (int j = 0; j < {DIM}; j++) {{
            output[i][j] = gamma[j] * input[i][j] / rms;
        }}
    }}
}}
