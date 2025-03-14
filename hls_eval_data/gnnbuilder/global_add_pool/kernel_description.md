Kernel Description:
The `global_add_pool` kernel is designed to perform a global addition pooling operation on a set of node embeddings. The kernel takes a table of node embeddings and sums them across all nodes to produce a single pooled embedding vector. This operation is commonly used in graph neural networks to aggregate information from all nodes in a graph into a single representation. The kernel initializes the pooled embedding vector to zero and then iteratively adds each node's embedding to the corresponding elements of the pooled embedding vector.

The kernel is designed to handle a maximum of `MAX_NODES` nodes, each with an embedding of size `EMB_SIZE`. The data type for the embeddings is defined as `T_data`, which is a `float` in this case. The kernel ensures that the pooled embedding is correctly computed even when the number of nodes is less than the maximum allowed by initializing the pooled embedding to zero and iterating only over the actual number of nodes provided.

---

Top-Level Function: `global_add_pool`

Complete Function Signature of the Top-Level Function:
`void global_add_pool(int num_nodes, T_data node_embedding_table[MAX_NODES][EMB_SIZE], T_data pooled_embedding[EMB_SIZE]);`

Inputs:
- `num_nodes`: An integer representing the number of nodes in the graph. It specifies how many rows of the `node_embedding_table` should be considered for the summation. The value of `num_nodes` should be between 1 and `MAX_NODES` (inclusive).
- `node_embedding_table`: A 2D array of type `T_data` with dimensions `MAX_NODES x EMB_SIZE`. Each row of this table represents the embedding of a node in the graph. The actual number of rows used is determined by `num_nodes`.

Outputs:
- `pooled_embedding`: A 1D array of type `T_data` with size `EMB_SIZE`. This array will store the result of summing the embeddings of all nodes. Each element of this array is the sum of the corresponding elements from all node embeddings.

Important Data Structures and Data Types:
- `node_embedding_table`: A 2D array of type `T_data` with dimensions `MAX_NODES x EMB_SIZE`. Each element of this array is a `float` representing a component of a node's embedding.
- `pooled_embedding`: A 1D array of type `T_data` with size `EMB_SIZE`. Each element of this array is a `float` representing the sum of the corresponding components from all node embeddings.

Sub-Components:
- None