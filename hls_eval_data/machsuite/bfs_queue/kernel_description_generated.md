Kernel Description:
The Breadth-First Search (BFS) algorithm is a graph traversal technique that explores a graph level by level, starting from a given starting node. The algorithm computes the shortest distance from the starting node to all other nodes in the graph. The design is optimized for parallel execution on multi-core CPUs and GPUs. The algorithm uses a circular buffer, implemented as a fixed-size array, to store nodes to be processed in the BFS traversal. The algorithm iterates over the nodes in the queue, processing each node and its neighbors, and updates the level and level_counts arrays as necessary. The level array stores the shortest distance from the starting node to each node, and the level_counts array stores the number of nodes at each distance level.

The algorithm can be represented by the following equation:
$$
\text{level}[i] = \min(\text{level}[i], \text{level}[j] + 1)
$$
where $i$ is the current node, $j$ is a neighbor of $i$, and $\text{level}[i]$ is the shortest distance from the starting node to node $i$.

The algorithm has several key components, including the queue, which stores nodes to be processed, and the level and level_counts arrays, which store the shortest distances and node counts, respectively. The algorithm also has several key steps, including initializing the level and level_counts arrays, processing each node in the queue, and updating the level and level_counts arrays as necessary.

The design uses several data structures, including the node_t and edge_t structs, which represent nodes and edges in the graph, respectively. The node_t struct has two fields, edge_begin and edge_end, which represent the range of edges connected to the node. The edge_t struct has one field, dst, which represents the destination node of the edge. The design also uses several data types, including the level_t and node_index_t types, which represent the shortest distance from the starting node to a node and the index of a node, respectively.

The algorithm has several implementation quirks and edge cases, including the use of a circular buffer to implement the queue, and the need to handle the case where a node has no neighbors. The algorithm also has several design decisions, including the choice of data structures and data types, and the optimization of the algorithm for parallel execution on multi-core CPUs and GPUs.

---

Top-Level Function: `bfs`

Complete Function Signature of the Top-Level Function:
`void bfs(node_t nodes[N_NODES], edge_t edges[N_EDGES], node_index_t starting_node, level_t level[N_NODES], edge_index_t level_counts[N_LEVELS]);`

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