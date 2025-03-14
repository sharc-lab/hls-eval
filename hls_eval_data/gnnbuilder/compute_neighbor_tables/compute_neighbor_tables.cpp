#include "compute_neighbor_tables.h"

void compute_neighbor_tables(
    int edge_list[MAX_EDGES][2],
    int in_degree_table[MAX_NODES],
    int out_degree_table[MAX_NODES],
    int neighbor_table_offsets[MAX_NODES],
    int neighbor_table[MAX_EDGES],
    int num_nodes,
    int num_edges) {

#pragma HLS INLINE off

    // compute neighbor table offsets
    // cumulative sum of in_degree_table
    // also store values temp array for later
    int neightbor_table_offsets_temp[MAX_NODES];
    neighbor_table_offsets[0] = 0;
    neightbor_table_offsets_temp[0] = 0;
    for (int i = 1; i < num_nodes; i++) {
#pragma HLS loop_tripcount min = 1 max = NUM_NODES_GUESS
        int csum = neighbor_table_offsets[i - 1] + in_degree_table[i - 1];
        neighbor_table_offsets[i] = csum;
        neightbor_table_offsets_temp[i] = csum;
    }

    // compute neighbor table
    for (int i = 0; i < num_edges; i++) {
#pragma HLS loop_tripcount min = 1 max = NUM_EDGES_GUESS
#pragma HLS PIPELINE off
        int source = edge_list[i][0];
        int dest = edge_list[i][1];

        int offset = neightbor_table_offsets_temp[dest];
        neighbor_table[offset] = source;
        neightbor_table_offsets_temp[dest]++;
    }
}