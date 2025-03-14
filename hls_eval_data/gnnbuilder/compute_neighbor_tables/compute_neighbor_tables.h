#define MAX_NODES 100
#define MAX_EDGES 1000
#define NUM_NODES_GUESS 50
#define NUM_EDGES_GUESS 500

void compute_neighbor_tables(
    int edge_list[MAX_EDGES][2],
    int in_degree_table[MAX_NODES],
    int out_degree_table[MAX_NODES],
    int neighbor_table_offsets[MAX_NODES],
    int neighbor_table[MAX_EDGES],
    int num_nodes,
    int num_edges);