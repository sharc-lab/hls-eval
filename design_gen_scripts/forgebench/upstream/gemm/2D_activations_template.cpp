
/*
 * Auto-generated Activation Functions for CNNs (3D version)
 * 
 * Data type: {DATA_TYPE}
 * Tensor dimensions: [{H}][{W}]
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
    data_t input[{H}][{W}],
    data_t output[{H}][{W}]
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            output[i][j] = (input[i][j] > 0) ? input[i][j] : (data_t)0;
        }}
    }}
}}
/*==== RELU FUNCTION END ====*/

/*==== LEAKY_RELU FUNCTION START ====*/
void leaky_relu(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}],
    data_t alpha
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            output[i][j] = (input[i][j] >= 0) ? input[i][j] : alpha * input[i][j];
        }}
    }}
}}
/*==== LEAKY_RELU FUNCTION END ====*/

/*==== PRELU FUNCTION START ====*/
void prelu(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}],
    data_t alpha
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            output[i][j] = (input[i][j] >= 0) ? input[i][j] : alpha * input[i][j];
        }}
    }}
}}
/*==== PRELU FUNCTION END ====*/

/*==== RRELU FUNCTION START ====*/
void rrelu(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}],
    data_t lower,
    data_t upper
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            if (input[i][j] >= 0) {{
                output[i][j] = input[i][j];
            }} else {{
                data_t ralpha = (lower + upper) / 2; // fixed value for demonstration
                output[i][j] = ralpha * input[i][j];
            }}
        }}
    }}
}}
/*==== RRELU FUNCTION END ====*/

/*==== THRESHOLDED_RELU FUNCTION START ====*/
void thresholded_relu(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}],
    data_t theta
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            output[i][j] = (input[i][j] > theta) ? input[i][j] : (data_t)0;
        }}
    }}
}}
/*==== THRESHOLDED_RELU FUNCTION END ====*/

/*==== RELU6 FUNCTION START ====*/
void relu6(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}],
    data_t cap  // cap value, typically 6
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            data_t temp = (input[i][j] > 0) ? input[i][j] : (data_t)0;
            output[i][j] = (temp < cap) ? temp : cap;
        }}
    }}
}}
/*==== RELU6 FUNCTION END ====*/

/*==== SIGMOID FUNCTION START ====*/
void sigmoid(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}]
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            output[i][j] = (data_t)1 / ((data_t)1 + hls::exp(-input[i][j]));
        }}
    }}
}}
/*==== SIGMOID FUNCTION END ====*/

/*==== TANH FUNCTION START ====*/
void tanh_act(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}]
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            output[i][j] = hls::tanh(input[i][j]);
        }}
    }}
}}
/*==== TANH FUNCTION END ====*/

/*==== ELU FUNCTION START ====*/
void elu(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}],
    data_t alpha  // ELU parameter
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            if (input[i][j] >= 0) {{
                output[i][j] = input[i][j];
            }} else {{
                output[i][j] = alpha * (hls::exp(input[i][j]) - 1);
            }}
        }}
    }}
}}
/*==== ELU FUNCTION END ====*/

/*==== SELU FUNCTION START ====*/
void selu(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}],
    data_t alpha,  // SELU alpha parameter
    data_t lambda  // SELU lambda parameter
)
{{
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            if (input[i][j] >= 0) {{
                output[i][j] = lambda * input[i][j];
            }} else {{
                output[i][j] = lambda * alpha * (hls::exp(input[i][j]) - 1);
            }}
        }}
    }}
}}
/*==== SELU FUNCTION END ====*/

/*==== GELU FUNCTION START ====*/
void gelu(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}]
)
{{
    // Approximation: 0.5 * x * (1 + tanh(sqrt(2/pi)*(x + 0.044715*x^3)))
    const data_t sqrt_2_over_pi = hls::sqrt((data_t)2/(data_t)3.141592653589793);
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            data_t x = input[i][j];
            data_t x_cube = x * x * x;
            data_t tanh_arg = sqrt_2_over_pi * (x + 0.044715 * x_cube);
            output[i][j] = 0.5 * x * (1 + hls::tanh(tanh_arg));
        }}
    }}
}}
/*==== GELU FUNCTION END ====*/

/*==== SWISH FUNCTION START ====*/
void swish(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}]
)
{{
    // Swish: x * sigmoid(x)
    for (int i = 0; i < {H}; i++) {{
        for (int j = 0; j < {W}; j++) {{
            data_t sig = (data_t)1 / ((data_t)1 + hls::exp(-input[i][j]));
            output[i][j] = input[i][j] * sig;
        }}
    }}
}}
/*==== SWISH FUNCTION END ====*/

/*==== SOFTMAX FUNCTION START ====*/
void softmax(
    data_t input[{H}][{W}],
    data_t output[{H}][{W}]
)
{{
    // Compute softmax rowwise. Subtract the row max before exp for numerical
    // stability: softmax is shift-invariant, so this is mathematically identical
    // but avoids exp() overflowing to inf (and the normalization to nan) when the
    // pre-softmax activations are large.
    for (int i = 0; i < {H}; i++) {{
        data_t max_val = input[i][0];
        for (int j = 1; j < {W}; j++) {{
            if (input[i][j] > max_val) max_val = input[i][j];
        }}

        data_t sum = 0;
        for (int j = 0; j < {W}; j++) {{
            output[i][j] = hls::exp(input[i][j] - max_val);
            sum += output[i][j];
        }}

        for (int j = 0; j < {W}; j++) {{
            output[i][j] /= sum;
        }}
    }}
}}
/*==== SOFTMAX FUNCTION END ====*/




