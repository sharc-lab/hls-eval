#include "update_knn.h"

int popcount(WholeDigitType x) {
    // most straightforward implementation
    // actually not bad on FPGA
    int cnt = 0;
    for (int i = 0; i < 256; i++)
        cnt = cnt + x[i];

    return cnt;
}

void update_knn(
    WholeDigitType test_inst,
    WholeDigitType train_inst,
    int min_distances[K_CONST]) {

    // Compute the difference using XOR
    WholeDigitType diff = test_inst ^ train_inst;

    int dist = 0;

    dist = popcount(diff);

    int max_dist = 0;
    int max_dist_id = K_CONST + 1;
    int k = 0;

// Find the max distance
FIND_MAX_DIST:
    for (int k = 0; k < K_CONST; ++k) {
        if (min_distances[k] > max_dist) {
            max_dist = min_distances[k];
            max_dist_id = k;
        }
    }

    // Replace the entry with the max distance
    if (dist < max_dist)
        min_distances[max_dist_id] = dist;

    return;
}
