#include "global_add_pool.h"

void global_add_pool(
    int num_nodes,
    T_data node_embedding_table[MAX_NODES][EMB_SIZE],
    T_data pooled_embedding[EMB_SIZE]) {
#pragma HLS INLINE off

    // Initialize pooled_embedding to zero
    for (int i = 0; i < EMB_SIZE; i++) {
#pragma HLS UNROLL
        pooled_embedding[i] = 0;
    }

    // Sum embeddings across nodes
    for (int i = 0; i < num_nodes; i++) {
#pragma HLS loop_tripcount min = 1 max = MAX_NODES
        for (int j = 0; j < EMB_SIZE; j++) {
            pooled_embedding[j] += node_embedding_table[i][j];
        }
    }
}