Kernel Description:
The Breadth-First Search (BFS) algorithm is a graph traversal technique that explores a graph level by level, starting from a given source node. The algorithm works by maintaining a queue of nodes to visit, where each node is added to the queue when it is first visited. The algorithm then iteratively visits each node in the queue, adding its unvisited neighbors to the queue. This process continues until all reachable nodes have been visited. The BFS algorithm is commonly used in many applications, including network topology discovery, web crawlers, and social network analysis.

In this implementation, the BFS algorithm is optimized for large graphs and uses a bulk-synchronous parallel approach to achieve high performance. The algorithm starts by initializing the level of the starting node to 0 and the level counts to 1. It then iterates over the levels of the graph, starting from the starting node and exploring the graph level by level. At each level, the algorithm adds unmarked neighbors to the next level and updates the level counts.

The algorithm uses the following data structures:
- `node_t`: a struct representing a node in the graph, with `edge_begin` and `edge_end` fields indicating the range of edges connected to the node.
- `edge_t`: a struct representing an edge in the graph, with a `dst` field indicating the destination node of the edge.
- `level_t`: an 8-bit signed integer type used to represent the level (distance from the starting node) of each node in the graph.
- `edge_index_t`: a 64-bit unsigned integer type used to represent edge indices.
- `node_index_t`: a 64-bit unsigned integer type used to represent node indices.

The algorithm can be represented by the following equation:
$$
level[v] = \min\{level[u] + 1\}
$$
where $u$ is a neighbor of $v$ and $level[u]$ is the level of node $u$.

The time complexity of the BFS algorithm is $O(|E| + |V|)$, where $|E|$ is the number of edges and $|V|$ is the number of vertices in the graph. The space complexity is $O(|V|)$, as we need to store the level of each node.

---

Top-Level Function: `bfs`

Complete Function Signature of the Top-Level Function:
`void bfs(node_t nodes[N_NODES], edge_t edges[N_EDGES], node_index_t starting_node, level_t level[N_NODES], edge_index_t level_counts[N_LEVELS]);`

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
- `node_t`: a struct representing a node in the graph, with `edge_begin` and `edge_end` fields indicating the range of edges connected to the node. The size of `node_t` is 16 bytes, with `edge_begin` and `edge_end` fields each occupying 8 bytes.
- `edge_t`: a struct representing an edge in the graph, with a `dst` field indicating the destination node of the edge. The size of `edge_t` is 8 bytes, with the `dst` field occupying 8 bytes.
- `level_t`: an 8-bit signed integer type used to represent the level (distance from the starting node) of each node in the graph.
- `edge_index_t`: a 64-bit unsigned integer type used to represent edge indices.
- `node_index_t`: a 64-bit unsigned integer type used to represent node indices.

Sub-Components:
- `loop_horizons`: a loop that iterates over the levels of the graph, starting from the starting node and exploring the graph level by level.
    - Signature: `for (horizon = 0; horizon < N_LEVELS; horizon++)`
    - Details: This loop is the outermost loop of the BFS algorithm and is responsible for iterating over the levels of the graph. At each level, the algorithm adds unmarked neighbors to the next level and updates the level counts.
- `loop_nodes`: a loop that iterates over the nodes in the current level, adding unmarked neighbors to the next level.
    - Signature: `for (n = 0; n < N_NODES; n++)`
    - Details: This loop is responsible for iterating over the nodes in the current level and adding unmarked neighbors to the next level.
- `loop_neighbors`: a loop that iterates over the edges connected to a node, marking unmarked neighbors and updating the level counts.
    - Signature: `for (e = tmp_begin; e < tmp_end; e++)`
    - Details: This loop is responsible for iterating over the edges connected to a node and marking unmarked neighbors. It also updates the level counts by incrementing the count of nodes at the next level.