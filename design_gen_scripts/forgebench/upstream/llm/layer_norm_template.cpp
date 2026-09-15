

void layer_norm(
    data_t input[{SEQ_LENGTH}][{DIM}],
    data_t gamma[{DIM}],
    data_t beta[{DIM}],
    data_t output[{SEQ_LENGTH}][{DIM}]
)
{{
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        // Compute mean for the i-th sequence element
        data_t sum = (data_t)0;
        for (int j = 0; j < {DIM}; j++) {{
            sum += input[i][j];
        }}
        data_t mean = sum / {DIM};

        // Compute variance for the i-th sequence element
        data_t var_sum = (data_t)0;
        for (int j = 0; j < {DIM}; j++) {{
            data_t diff = input[i][j] - mean;
            var_sum += diff * diff;
        }}
        data_t variance = var_sum / {DIM};

        // Normalize and scale: output = gamma * (x - mean) / sqrt(variance + epsilon) + beta
        for (int j = 0; j < {DIM}; j++) {{
            output[i][j] = gamma[j] * ((input[i][j] - mean) / hls::sqrt(variance + (data_t){EPSILON})) + beta[j];
        }}
    }}
}}
