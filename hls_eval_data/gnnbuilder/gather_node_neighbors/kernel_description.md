Kernel Description:
The `gather_node_neighbors` kernel is designed to gather the neighbors of a specific node in a graph. The graph is represented using an adjacency list format, where `neighbor_table_offsets` provides the starting index in `neighbor_table` for each node's neighbors, and `neighbor_table` contains the actual neighbor indices. The kernel takes a node index and its in-degree (number of neighbors) as inputs and fills an array with the indices of the node's neighbors. The kernel is optimized for high-level synthesis (HLS) with specific pragmas to control inlining and loop behavior.

The algorithm works as follows:
1. Retrieve the starting index of the node's neighbors from `neighbor_table_offsets`.
2. Iterate over the range of the node's in-degree.
3. For each iteration, calculate the current index in `neighbor_table` by adding the loop index to the starting index.
4. Copy the neighbor index from `neighbor_table` to the `node_neighbors` array.

---

Top-Level Function: `gather_node_neighbors`

Complete Function Signature of the Top-Level Function:
`void gather_node_neighbors(int node, int node_in_degree, int node_neighbors[MAX_NODES], int neighbor_table_offsets[MAX_NODES], int neighbor_table[MAX_EDGES]);`

Inputs:
- `node`: An integer representing the index of the node whose neighbors are to be gathered. The data type is `int`, and the valid range is from 0 to `MAX_NODES - 1`.
- `node_in_degree`: An integer representing the number of neighbors the node has. The data type is `int`, and the valid range is from 0 to `DEGREE_GUESS`.
- `node_neighbors`: An array of integers where the indices of the node's neighbors will be stored. The data type is `int`, and the array size is `MAX_NODES`. Only the first `node_in_degree` elements of this array will be used.
- `neighbor_table_offsets`: An array of integers representing the starting index in `neighbor_table` for each node's neighbors. The data type is `int`, and the array size is `MAX_NODES`.
- `neighbor_table`: An array of integers representing the neighbor indices for all nodes in the graph. The data type is `int`, and the array size is `MAX_EDGES`.

Outputs:
- `node_neighbors`: The array is modified in place to contain the indices of the node's neighbors. The first `node_in_degree` elements of this array will be filled with the neighbor indices.

Important Data Structures and Data Types:
- `node_neighbors`: An array of integers with a size of `MAX_NODES`. It is used to store the indices of the node's neighbors.
- `neighbor_table_offsets`: An array of integers with a size of `MAX_NODES`. It provides the starting index in `neighbor_table` for each node's neighbors.
- `neighbor_table`: An array of integers with a size of `MAX_EDGES`. It contains the actual neighbor indices for all nodes in the graph.

Sub-Components:
- None