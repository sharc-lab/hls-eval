#include "global_add_pool.h"

int main() {
    int num_nodes = 10;
    T_data node_embedding_table[MAX_NODES][EMB_SIZE];
    T_data pooled_embedding[EMB_SIZE] = {0};

    for (int i = 0; i < num_nodes; i++) {
        for (int j = 0; j < EMB_SIZE; j++) {
            node_embedding_table[i][j] = T_data(i + j) / (num_nodes * EMB_SIZE);
        }
    }

    global_add_pool(num_nodes, node_embedding_table, pooled_embedding);

    return 0;
}