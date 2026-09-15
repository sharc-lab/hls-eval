
// Inference-time dropout is the identity: dropout is disabled at evaluation time
// (with inverted dropout, the 1/(1-p) scaling is already folded in at training
// time). This benchmark emits inference designs, so dropout is a passthrough.
// dropout_prob and seed are kept in the signature for call-site compatibility but
// are intentionally unused.
void dropout(
    data_t input[{SEQ_LENGTH}][{DIM}],
    data_t output[{SEQ_LENGTH}][{DIM}],
    data_t dropout_prob,
    unsigned int seed
)
{{
    (void)dropout_prob;
    (void)seed;
    for (int i = 0; i < {SEQ_LENGTH}; i++) {{
        for (int j = 0; j < {DIM}; j++) {{
            output[i][j] = input[i][j];
        }}
    }}
}}
