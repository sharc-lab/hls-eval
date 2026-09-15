
void rope(
    data_t input[{SEQ_LENGTH}][{HIDDEN_DIM}],
    data_t output[{SEQ_LENGTH}][{HIDDEN_DIM}]
)
{{
    // Apply RoPE to each sequence element.
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        for (int k = 0; k < {HIDDEN_DIM}; k += 2) {{
            // Compute frequency scaling factor for this pair.
            // Here we use: freq = 10000^(- (2*k) / HIDDEN_DIM ).
            data_t freq = (data_t)hls::powf(10000.0f, -((float)k) / (float){HIDDEN_DIM});
            data_t angle = i * freq;
            data_t cos_val = hls::cos(angle);
            data_t sin_val = hls::sin(angle);
            // Retrieve the pair of values.
            data_t x0 = input[i][k];
            data_t x1 = input[i][k+1];
            // Apply the rotation.
            output[i][k]   = x0 * cos_val - x1 * sin_val;
            output[i][k+1] = x0 * sin_val + x1 * cos_val;
        }}
    }}
}}
