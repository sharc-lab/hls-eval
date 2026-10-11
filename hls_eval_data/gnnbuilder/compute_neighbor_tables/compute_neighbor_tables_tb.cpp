#include "compute_neighbor_tables.h"
#include <iostream>

static int failures = 0;
static int checked = 0;

static void check(int actual, int expected, int nodes, int edges, const char* field, int i) {
    ++checked;
    if (actual != expected) {
        ++failures;
        std::cerr << "neighbors nodes=" << nodes << " edges=" << edges
                  << ' ' << field << '[' << i << "] expected=" << expected
                  << " actual=" << actual << '\n';
    }
}

static void run_case(int nodes, int edges, int mode) {
    int edge_list[MAX_EDGES][2];
    int indegree[MAX_NODES] = {}, outdegree[MAX_NODES] = {};
    int offsets[MAX_NODES], neighbors[MAX_EDGES];
    int expected_offsets[MAX_NODES], expected_neighbors[MAX_EDGES];
    for (int i = 0; i < MAX_NODES; ++i) offsets[i] = -7001;
    for (int e = 0; e < MAX_EDGES; ++e) {
        edge_list[e][0] = edge_list[e][1] = 0;
        neighbors[e] = -7003;
    }
    for (int e = 0; e < edges; ++e) {
        int src, dst;
        if (mode == 0) { src = (e * 7 + e / 3) % nodes; dst = (e * 11 + 1) % nodes; }
        else if (mode == 1) { src = e % nodes; dst = src; } // self-loops
        else if (mode == 2) { src = (e / 2) % nodes; dst = nodes - 1; } // duplicate edges + isolated nodes
        else { src = (e * 3 + 1) % nodes; dst = (e % 2) * (nodes - 1); }
        edge_list[e][0] = src;
        edge_list[e][1] = dst;
        ++outdegree[src];
        ++indegree[dst];
    }
    // Independent destination-group scan, not the kernel's prefix/cursor algorithm.
    int position = 0;
    for (int node = 0; node < nodes; ++node) {
        expected_offsets[node] = position;
        for (int e = 0; e < edges; ++e)
            if (edge_list[e][1] == node) expected_neighbors[position++] = edge_list[e][0];
    }
    compute_neighbor_tables(edge_list, indegree, outdegree, offsets, neighbors, nodes, edges);
    for (int node = 0; node < nodes; ++node)
        check(offsets[node], expected_offsets[node], nodes, edges, "offset", node);
    for (int e = 0; e < edges; ++e)
        check(neighbors[e], expected_neighbors[e], nodes, edges, "neighbor", e);
}

int main() {
    run_case(1, 0, 0);
    run_case(1, 1, 1);
    run_case(2, 0, 0);
    run_case(2, 8, 2);
    run_case(7, 17, 0);
    run_case(7, 31, 3);
    run_case(MAX_NODES, 0, 0);
    run_case(MAX_NODES, MAX_EDGES, 0);
    run_case(MAX_NODES, MAX_EDGES, 1);
    run_case(MAX_NODES, MAX_EDGES, 2);
    run_case(3, 5, 0); // Different sizes on a later invocation.
    std::cout << "GNN_FIXTURE fields=" << checked << " failures=" << failures << '\n';
    return failures ? 1 : 0;
}
