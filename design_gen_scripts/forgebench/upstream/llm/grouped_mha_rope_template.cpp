/*
 * Auto-generated Grouped Multi-head Attention (with optional inline RoPE)
 *
 * Input     : [{SEQ_LENGTH}][{DIM_IN}]
 * W_q/k/v   : [{DIM_OUT}][{DIM_IN}], DIM_OUT = NUM_HEADS * HEAD_DIM
 * Output    : [{SEQ_LENGTH}][{DIM_OUT}]
 *
 * Data type : {DATA_TYPE}
 * Num Heads : {NUM_HEADS}
 * Head Dim  : {HEAD_DIM}
 */

 void grouped_multihead_attention(
    data_t input[{SEQ_LENGTH}][{DIM_IN}],
    data_t W_q[{DIM_OUT}][{DIM_IN}],
    data_t W_k[{DIM_OUT}][{DIM_IN}],
    data_t W_v[{DIM_OUT}][{DIM_IN}],
    data_t output[{SEQ_LENGTH}][{DIM_OUT}],
    int groups
)
{{
    const int num_heads = {NUM_HEADS};   // total number of heads (must equal DIM_OUT / HEAD_DIM)
    const int head_dim = {HEAD_DIM};       // dimension per head
    const int heads_per_group = num_heads / groups;
    const data_t scale = (data_t)1.0 / hls::sqrt((data_t)head_dim);

    data_t Q[{SEQ_LENGTH}][{DIM_OUT}];
    data_t K[{SEQ_LENGTH}][{DIM_OUT}];
    data_t V[{SEQ_LENGTH}][{DIM_OUT}];

    // Compute Q, K, V
    for (int seq = 0; seq < {SEQ_LENGTH}; seq++) {{
        for (int dout = 0; dout < {DIM_OUT}; dout++) {{
            Q[seq][dout] = 0;
            K[seq][dout] = 0;
            V[seq][dout] = 0;
            for (int din = 0; din < {DIM_IN}; din++) {{
                Q[seq][dout] += input[seq][din] * W_q[dout][din];
                K[seq][dout] += input[seq][din] * W_k[dout][din];
                V[seq][dout] += input[seq][din] * W_v[dout][din];
            }}
        }}
    }}

    /*==== BEGIN OPTIONAL ROPE LOGIC ====*/
    {ROPE_INLINE}
    /*==== END OPTIONAL ROPE LOGIC ====*/

    // Compute Attention per head in groups.
    for (int g = 0; g < groups; g++) {{
        for (int h = 0; h < heads_per_group; h++) {{
            int head_index = g * heads_per_group + h;
            data_t scores[{SEQ_LENGTH}][{SEQ_LENGTH}];

            // Scaled Dot-product: Q x K^T for head head_index
            for (int i = 0; i < {SEQ_LENGTH}; i++) {{
                for (int j = 0; j < {SEQ_LENGTH}; j++) {{
                    scores[i][j] = 0;
                    for (int d = 0; d < head_dim; d++) {{
                        int idx = head_index * head_dim + d;
                        scores[i][j] += Q[i][idx] * K[j][idx];
                    }}
                    scores[i][j] *= scale;
                }}
            }}

            // Softmax for this head.
            for (int i = 0; i < {SEQ_LENGTH}; i++) {{
                data_t sum_exp = 0;
                data_t max_score = scores[i][0];
                for (int j = 1; j < {SEQ_LENGTH}; j++) {{
                    if (scores[i][j] > max_score)
                        max_score = scores[i][j];
                }}
                for (int j = 0; j < {SEQ_LENGTH}; j++) {{
                    scores[i][j] = hls::exp(scores[i][j] - max_score);
                    sum_exp += scores[i][j];
                }}
                for (int j = 0; j < {SEQ_LENGTH}; j++) {{
                    scores[i][j] /= sum_exp;
                }}
            }}

            // Compute context: scores x V for head head_index.
            for (int i = 0; i < {SEQ_LENGTH}; i++) {{
                for (int d = 0; d < head_dim; d++) {{
                    data_t context = 0;
                    for (int j = 0; j < {SEQ_LENGTH}; j++) {{
                        context += scores[i][j] * V[j][head_index * head_dim + d];
                    }}
                    output[i][head_index * head_dim + d] = context;
                }}
            }}
        }}
    }}
}}