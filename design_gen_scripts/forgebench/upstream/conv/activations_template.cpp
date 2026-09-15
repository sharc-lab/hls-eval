
/*
 * Auto-generated Activation Functions for CNNs (3D version)
 * 
 * Data type: {DATA_TYPE}
 * Tensor dimensions: [{C}][{H}][{W}]
 *
 * Available functions:
 *   - relu
 *   - leaky_relu
 *   - prelu
 *   - rrelu
 *   - thresholded_relu
 *   - relu6
 *   - sigmoid
 *   - tanh_act
 *   - elu
 *   - selu
 *   - gelu
 *   - swish
 *   - softmax
 */

/*==== RELU FUNCTION START ====*/
void relu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                output[c][i][j] = (input[c][i][j] > 0) ? input[c][i][j] : (data_t)0;
            }}
        }}
    }}
}}
/*==== RELU FUNCTION END ====*/

/*==== LEAKY_RELU FUNCTION START ====*/
void leaky_relu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}],
    data_t alpha
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                output[c][i][j] = (input[c][i][j] >= 0) ? input[c][i][j] : alpha * input[c][i][j];
            }}
        }}
    }}
}}
/*==== LEAKY_RELU FUNCTION END ====*/

/*==== PRELU FUNCTION START ====*/
void prelu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}],
    data_t alpha[{C}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                output[c][i][j] = (input[c][i][j] >= 0) ? input[c][i][j] : alpha[c] * input[c][i][j];
            }}
        }}
    }}
}}
/*==== PRELU FUNCTION END ====*/

/*==== RRELU FUNCTION START ====*/
void rrelu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}],
    data_t lower,
    data_t upper
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                if (input[c][i][j] >= 0) {{
                    output[c][i][j] = input[c][i][j];
                }} else {{
                    data_t ralpha = (lower + upper) / (data_t)2; // fixed value for demonstration
                    output[c][i][j] = ralpha * input[c][i][j];
                }}
            }}
        }}
    }}
}}
/*==== RRELU FUNCTION END ====*/

/*==== THRESHOLDED_RELU FUNCTION START ====*/
void thresholded_relu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}],
    data_t theta
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                output[c][i][j] = (input[c][i][j] > theta) ? input[c][i][j] : (data_t)0;
            }}
        }}
    }}
}}
/*==== THRESHOLDED_RELU FUNCTION END ====*/

/*==== RELU6 FUNCTION START ====*/
void relu6(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}],
    data_t cap  // cap value, typically 6
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                data_t temp = (input[c][i][j] > 0) ? input[c][i][j] : (data_t)0;
                output[c][i][j] = (temp < cap) ? temp : cap;
            }}
        }}
    }}
}}
/*==== RELU6 FUNCTION END ====*/

/*==== SIGMOID FUNCTION START ====*/
void sigmoid(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                output[c][i][j] = (data_t)1 / ((data_t)1 + hls::exp(-input[c][i][j]));
            }}
        }}
    }}
}}
/*==== SIGMOID FUNCTION END ====*/

/*==== TANH FUNCTION START ====*/
void tanh_act(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                output[c][i][j] = hls::tanh(input[c][i][j]);
            }}
        }}
    }}
}}
/*==== TANH FUNCTION END ====*/

/*==== ELU FUNCTION START ====*/
void elu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}],
    data_t alpha  // ELU parameter
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                if (input[c][i][j] >= 0) {{
                    output[c][i][j] = input[c][i][j];
                }} else {{
                    output[c][i][j] = alpha * (hls::exp(input[c][i][j]) - 1);
                }}
            }}
        }}
    }}
}}
/*==== ELU FUNCTION END ====*/

/*==== SELU FUNCTION START ====*/
void selu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}],
    data_t alpha,  // SELU alpha parameter
    data_t lambda  // SELU lambda parameter
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                if (input[c][i][j] >= 0) {{
                    output[c][i][j] = lambda * input[c][i][j];
                }} else {{
                    output[c][i][j] = lambda * alpha * (hls::exp(input[c][i][j]) - 1);
                }}
            }}
        }}
    }}
}}
/*==== SELU FUNCTION END ====*/

/*==== GELU FUNCTION START ====*/
void gelu(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    // Approximation: 0.5 * x * (1 + tanh(sqrt(2/pi)*(x + 0.044715*x^3)))
    const data_t sqrt_2_over_pi = hls::sqrt((data_t)2/(data_t)3.141592653589793);
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                data_t x = input[c][i][j];
                data_t x_cube = x * x * x;
                data_t tanh_arg = sqrt_2_over_pi * (x + 0.044715 * x_cube);
                output[c][i][j] = 0.5 * x * (1 + hls::tanh(tanh_arg));
            }}
        }}
    }}
}}
/*==== GELU FUNCTION END ====*/

/*==== SWISH FUNCTION START ====*/
void swish(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    // Swish: x * sigmoid(x)
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                data_t sig = (data_t)1 / ((data_t)1 + hls::exp(-input[c][i][j]));
                output[c][i][j] = input[c][i][j] * sig;
            }}
        }}
    }}
}}
/*==== SWISH FUNCTION END ====*/

/*==== SOFTMAX FUNCTION START ====*/
void softmax(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    // Compute softmax along the channel dimension for each spatial location.
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            data_t sum = 0;
            // First pass: compute exponentials and sum
            for (int c = 0; c < {C}; c++) {{
                output[c][i][j] = hls::exp(input[c][i][j]);
                sum += output[c][i][j];
            }}
            // Second pass: normalize
            for (int c = 0; c < {C}; c++) {{
                output[c][i][j] /= sum;
            }}
        }}
    }}
}}
/*==== SOFTMAX FUNCTION END ====*/

/*==== HARDSIGMOID FUNCTION START ====*/
void hardsigmoid(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                data_t x = input[c][i][j];
                if (x <= (data_t)-3) {{
                    output[c][i][j] = (data_t)0;
                }} else if (x >= (data_t)3) {{
                    output[c][i][j] = (data_t)1;
                }} else {{
                    output[c][i][j] = (x + (data_t)3) / (data_t)6;
                }}
            }}
        }}
    }}
}}
/*==== HARDSIGMOID FUNCTION END ====*/

/*==== HARDSWISH FUNCTION START ====*/
void hardswish(
    data_t input[{C}][{H}][{W}],
    data_t output[{C}][{H}][{W}]
)
{{
    for (int c = 0; c < {C}; c++) {{
        for (int i = 0; i < {H}; i++) {{
            for (int j = 0; j < {W}; j++) {{
                data_t x = input[c][i][j];
                // inline HardSigmoid
                data_t hsig = (data_t)0;
                if (x <= (data_t)-3) {{
                    hsig = (data_t)0;
                }} else if (x >= (data_t)3) {{
                    hsig = (data_t)1;
                }} else {{
                    hsig = (x + (data_t)3) / (data_t)6;
                }}
                // HardSwish(x) = x * HardSigmoid(x)
                output[c][i][j] = x * hsig;
            }}
        }}
    }}
}}
/*==== HARDSWISH FUNCTION END ====*/


