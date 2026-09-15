
void sliding_window_attention(
    data_t input[{SEQ_LENGTH}][{DIM_IN}],
    data_t W_q[{DIM_OUT}][{DIM_IN}],
    data_t W_k[{DIM_OUT}][{DIM_IN}],
    data_t W_v[{DIM_OUT}][{DIM_IN}],
    data_t output[{SEQ_LENGTH}][{DIM_OUT}],
    int window_size
)
{{
    const int num_heads = {NUM_HEADS};   // total number of heads (must equal DIM_OUT / HEAD_DIM)
    const int head_dim = {HEAD_DIM};       // dimension per head
    const data_t scale = (data_t)1.0 / hls::sqrt((data_t)head_dim);

    data_t Q[{SEQ_LENGTH}][{DIM_OUT}];
    data_t K[{SEQ_LENGTH}][{DIM_OUT}];
    data_t V[{SEQ_LENGTH}][{DIM_OUT}];

    // Compute Q, K, V
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        for (int d = 0; d < {DIM_OUT}; d++) {{
            Q[i][d] = 0;
            K[i][d] = 0;
            V[i][d] = 0;
            for (int j = 0; j < {DIM_IN}; j++) {{
                Q[i][d] += input[i][j] * W_q[d][j];
                K[i][d] += input[i][j] * W_k[d][j];
                V[i][d] += input[i][j] * W_v[d][j];
            }}
        }}
    }}

    /*==== BEGIN OPTIONAL ROPE LOGIC ====*/
    {ROPE_INLINE}
    /*==== END OPTIONAL ROPE LOGIC ====*/

    // Sliding window attention: for each head, each query attends only to a local window.
    for (int h = 0; h < num_heads; h++) {{
        for (int i = 0; i < {SEQ_LENGTH}; i++) {{
            // Determine window bounds
            int start = (i - window_size < 0) ? 0 : i - window_size;
            int end = (i + window_size >= {SEQ_LENGTH}) ? {SEQ_LENGTH} - 1 : i + window_size;
            data_t scores[{SEQ_LENGTH}]; // Allocate full length for simplicity

            // Compute scaled dot-product scores for indices within the window.
            for (int j = start; j <= end; j++) {{
                data_t sum = 0;
                for (int d = 0; d < head_dim; d++) {{
                    int idx = h * head_dim + d;
                    sum += Q[i][idx] * K[j][idx];
                }}
                scores[j] = sum * scale;
            }}

            // Apply softmax over the window.
            data_t max_val = scores[start];
            for (int j = start + 1; j <= end; j++) {{
                if (scores[j] > max_val)
                    max_val = scores[j];
            }}
            data_t sum_exp = 0;
            for (int j = start; j <= end; j++) {{
                scores[j] = hls::exp(scores[j] - max_val);
                sum_exp += scores[j];
            }}
            for (int j = start; j <= end; j++) {{
                scores[j] /= sum_exp;
            }}

            // Compute context vector for the current head.
            for (int d = 0; d < head_dim; d++) {{
                data_t context = 0;
                for (int j = start; j <= end; j++) {{
                    int idx = h * head_dim + d;
                    context += scores[j] * V[j][idx];
                }}
                output[i][h * head_dim + d] = context;
            }}
        }}
    }}
}}
