#define MAX_NODES 100
#define MAX_EDGES 1000
#define DEGREE_GUESS 10

void gather_node_neighbors(
    int node,
    int node_in_degree,
    int node_neighbors[MAX_NODES],
    int neighbor_table_offsets[MAX_NODES],
    int neighbor_table[MAX_EDGES]);