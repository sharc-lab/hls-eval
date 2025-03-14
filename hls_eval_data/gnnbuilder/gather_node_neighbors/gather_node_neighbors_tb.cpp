#include "gather_node_neighbors.h"

int main() {
    int node = 5;
    int node_in_degree = 5;
    int node_neighbors[MAX_NODES];
    int neighbor_table_offsets[MAX_NODES];
    int neighbor_table[MAX_EDGES];

    neighbor_table_offsets[5] = 7;
    for (int i = 0; i < MAX_EDGES; i++) {
        neighbor_table[7 + i] = i;
    }

    gather_node_neighbors(
        node,
        node_in_degree,
        node_neighbors,
        neighbor_table_offsets,
        neighbor_table);

    return 0;
}