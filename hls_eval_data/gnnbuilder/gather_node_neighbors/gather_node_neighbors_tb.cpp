#include "gather_node_neighbors.h"
#include <cstdio>
int main() {
    int failures = 0, checked = 0;
    const int nodes[] = {0, MAX_NODES - 1, 5, 7};
    const int degrees[] = {0, 1, 5, DEGREE_GUESS};
    for (int c = 0; c < 4; ++c) {
        int neighbors[MAX_NODES], offsets[MAX_NODES], table[MAX_EDGES];
        for (int i = 0; i < MAX_NODES; ++i) { neighbors[i] = -777; offsets[i] = 0; }
        for (int i = 0; i < MAX_EDGES; ++i) table[i] = (i * 7) % MAX_NODES;
        const int start = c == 3 ? MAX_EDGES - degrees[c] : 7;
        offsets[nodes[c]] = start;
        gather_node_neighbors(nodes[c], degrees[c], neighbors, offsets, table);
        for (int i = 0; i < degrees[c]; ++i) {
            ++checked;
            if (neighbors[i] != ((start + i) * 7) % MAX_NODES) ++failures;
        }
    }
    std::printf("GATHER fields=%d failures=%d\n", checked, failures);
    return failures ? 1 : 0;
}
