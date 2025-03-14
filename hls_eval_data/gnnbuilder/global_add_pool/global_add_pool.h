#define MAX_NODES 100
#define EMB_SIZE 16
#define T_data float

void global_add_pool(
    int num_nodes,
    T_data node_embedding_table[MAX_NODES][EMB_SIZE],
    T_data pooled_embedding[EMB_SIZE]);