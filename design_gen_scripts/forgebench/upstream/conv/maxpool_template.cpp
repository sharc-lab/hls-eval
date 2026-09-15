
/*
 * Auto-generated Max Pooling HLS Code
 *
 * Dimensions:
 *   Input  : [{C}][{H_IN}][{W_IN}]
 *   Output : [{C}][{H_OUT}][{W_OUT}]
 *   Pooling Window: [{K_H}][{K_W}]
 *   Stride: [{STRIDE_H}][{STRIDE_W}]
 *
 * Data type: {DATA_TYPE}
 */

void maxpool(
    data_t input[{C}][{H_IN}][{W_IN}],
    data_t output[{C}][{H_OUT}][{W_OUT}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H_OUT}; i++) {{
            for (int j = 0; j < {W_OUT}; j++) {{
                // Initialize max value from the top-left corner of the window
                data_t max_val = input[c][i * {STRIDE_H}][j * {STRIDE_W}];
                for (int kh = 0; kh < {K_H}; kh++) {{
                    for (int kw = 0; kw < {K_W}; kw++) {{
                        int row = i * {STRIDE_H} + kh;
                        int col = j * {STRIDE_W} + kw;
                        if (input[c][row][col] > max_val) {{
                            max_val = input[c][row][col];
                        }}
                    }}
                }}
                output[c][i][j] = max_val;
            }}
        }}
    }}
}}
