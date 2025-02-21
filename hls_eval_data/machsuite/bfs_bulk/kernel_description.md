## bfs_bulk

An implementation of the Breadth-First Search (BFS) algorithm for graph traversal. The algorithm starts from a given starting node and explores the graph level by level, marking each node with its distance from the starting node. The design is optimized for large graphs and uses a bulk-synchronous parallel approach to achieve high performance.

Top-Level Function: `bfs`

Inputs:

- `nodes`: an array of `node_t` structures, each representing a node in the graph, with `edge_begin` and `edge_end` fields indicating the range of edges connected to the node.
- `edges`: an array of `edge_t` structures, each representing an edge in the graph, with a `dst` field indicating the destination node of the edge.
- `starting_node`: a `node_index_t` value indicating the starting node of the BFS traversal.
- `level`: an array of `level_t` values, where each element represents the level (distance from the starting node) of the corresponding node in the graph.
- `level_counts`: an array of `edge_index_t` values, where each element represents the number of nodes at the corresponding level.

Outputs:

- `level`: the updated array of `level_t` values, where each element represents the level (distance from the starting node) of the corresponding node in the graph.
- `level_counts`: the updated array of `edge_index_t` values, where each element represents the number of nodes at the corresponding level.

Important Data Structures and Data Types:

- `node_t`: a struct representing a node in the graph, with `edge_begin` and `edge_end` fields indicating the range of edges connected to the node.
- `edge_t`: a struct representing an edge in the graph, with a `dst` field indicating the destination node of the edge.
- `level_t`: an 8-bit signed integer type used to represent the level (distance from the starting node) of each node in the graph.
- `edge_index_t`: a 64-bit unsigned integer type used to represent edge indices.
- `node_index_t`: a 64-bit unsigned integer type used to represent node indices.

Sub-Components:

- `loop_horizons`: a loop that iterates over the levels of the graph, starting from the starting node and exploring the graph level by level.
- `loop_nodes`: a loop that iterates over the nodes in the current level, adding unmarked neighbors to the next level.
- `loop_neighbors`: a loop that iterates over the edges connected to a node, marking unmarked neighbors and updating the level counts.