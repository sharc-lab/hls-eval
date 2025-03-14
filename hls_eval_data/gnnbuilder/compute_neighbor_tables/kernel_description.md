Kernel Description:
The `compute_neighbor_tables` kernel is designed to compute the neighbor tables for a directed graph. The graph is represented by an edge list, where each edge is defined by a source node and a destination node. The kernel calculates the in-degree and out-degree of each node, and constructs a neighbor table that lists the source nodes for each destination node. The neighbor table offsets are used to index into the neighbor table for each node.

The algorithm consists of two main steps:
1. **Compute Neighbor Table Offsets**: This step calculates the cumulative sum of the in-degree table to determine the starting index for each node's neighbors in the neighbor table. A temporary array `neightbor_table_offsets_temp` is used to store these cumulative sums temporarily.
2. **Compute Neighbor Table**: This step populates the neighbor table by iterating over the edge list. For each edge, the source node is added to the neighbor table at the position indicated by the corresponding offset in `neightbor_table_offsets_temp`, which is then incremented.

---

Top-Level Function: `compute_neighbor_tables`

Complete Function Signature of the Top-Level Function:
`void compute_neighbor_tables(int edge_list[MAX_EDGES][2], int in_degree_table[MAX_NODES], int out_degree_table[MAX_NODES], int neighbor_table_offsets[MAX_NODES], int neighbor_table[MAX_EDGES], int num_nodes, int num_edges);`

Inputs:
- `edge_list`: A 2D array of integers representing the edge list of the graph. Each element `edge_list[i][0]` is the source node and `edge_list[i][1]` is the destination node of the i-th edge. The data type is `int` and the layout is a 2D array with dimensions `[MAX_EDGES][2]`.
- `in_degree_table`: An array of integers representing the in-degree of each node. The data type is `int` and the layout is a 1D array with size `MAX_NODES`.
- `out_degree_table`: An array of integers representing the out-degree of each node. This input is not used in the current implementation but is included in the function signature. The data type is `int` and the layout is a 1D array with size `MAX_NODES`.
- `neighbor_table_offsets`: An array of integers that will store the starting index for each node's neighbors in the neighbor table. The data type is `int` and the layout is a 1D array with size `MAX_NODES`.
- `neighbor_table`: An array of integers that will store the source nodes for each destination node. The data type is `int` and the layout is a 1D array with size `MAX_EDGES`.
- `num_nodes`: An integer representing the number of nodes in the graph. The data type is `int`.
- `num_edges`: An integer representing the number of edges in the graph. The data type is `int`.

Outputs:
- `neighbor_table_offsets`: An array of integers that stores the starting index for each node's neighbors in the neighbor table. The data type is `int` and the layout is a 1D array with size `MAX_NODES`.
- `neighbor_table`: An array of integers that stores the source nodes for each destination node. The data type is `int` and the layout is a 1D array with size `MAX_EDGES`.

Important Data Structures and Data Types:
- `neightbor_table_offsets_temp`: An array of integers used to temporarily store the cumulative sums of the in-degree table. The data type is `int` and the layout is a 1D array with size `MAX_NODES`.

Sub-Components:
- None