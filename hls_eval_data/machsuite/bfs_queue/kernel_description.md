## bfs_queue

An implementation of the Breadth-First Search (BFS) algorithm for graph traversal. The algorithm explores a graph level by level, starting from a given starting node, and computes the shortest distance from the starting node to all other nodes in the graph. The design is optimized for parallel execution on multi-core CPUs and GPUs.

Top-Level Function: `bfs`

Inputs:

- `nodes`: an array of `node_t` structures, each representing a node in the graph, with `edge_begin` and `edge_end` fields indicating the range of edges connected to the node.
- `edges`: an array of `edge_t` structures, each representing an edge in the graph, with a `dst` field indicating the destination node of the edge.
- `starting_node`: a `node_index_t` value indicating the starting node of the BFS traversal.
- `level`: an array of `level_t` values, where `level[i]` represents the shortest distance from the starting node to node `i`.
- `level_counts`: an array of `edge_index_t` values, where `level_counts[i]` represents the number of nodes at distance `i` from the starting node.

Outputs:

- `level`: the updated array of shortest distances from the starting node to all nodes in the graph.
- `level_counts`: the updated array of node counts at each distance level.

Important Data Structures and Data Types:

- `node_t`: a struct representing a node in the graph, with `edge_begin` and `edge_end` fields indicating the range of edges connected to the node.
- `edge_t`: a struct representing an edge in the graph, with a `dst` field indicating the destination node of the edge.
- `level_t`: an 8-bit signed integer type representing the shortest distance from the starting node to a node.
- `node_index_t` and `edge_index_t`: 64-bit unsigned integer types representing node and edge indices, respectively.

Sub-Components:

- `queue`: a circular buffer implemented using a fixed-size array, used to store nodes to be processed in the BFS traversal.
- `init_levels`: a component that initializes the `level` array with maximum values.
- `init_horizons`: a component that initializes the `level_counts` array with zero values.
- `loop_queue`: a component that iterates over the nodes in the queue, processing each node and its neighbors.
- `loop_neighbors`: a component that iterates over the edges connected to a node, updating the `level` and `level_counts` arrays as necessary.