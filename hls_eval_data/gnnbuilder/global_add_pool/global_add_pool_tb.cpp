#include "global_add_pool.h"
#include <iostream>

static int failures = 0;
static int checked = 0;

static void run_case(int nodes, int mode) {
    T_data table[MAX_NODES][EMB_SIZE];
    T_data output[EMB_SIZE];
    T_data expected[EMB_SIZE];
    for (int j = 0; j < EMB_SIZE; ++j) {
        output[j] = T_data(1000 + j);
        long exact_scaled_sum = 0;
        for (int i = 0; i < MAX_NODES; ++i) {
            // Active values and their sums are exact binary fractions.
            int scaled = ((i * 17 + j * 13 + mode * 7) % 127) - 63;
            table[i][j] = i < nodes ? T_data(scaled) / 8 : T_data(4096 + j);
            if (i < nodes) exact_scaled_sum += scaled;
        }
        expected[j] = T_data(exact_scaled_sum) / 8;
    }
    if (mode == 7) {
        // Exactly specified sequential native-float additions: large+1-large.
        for (int j = 0; j < EMB_SIZE; ++j) {
            table[0][j] = T_data(16777216);
            table[1][j] = T_data(1);
            table[2][j] = T_data(-16777216);
            expected[j] = T_data(0);
        }
    }
    global_add_pool(nodes, table, output);
    for (int j = 0; j < EMB_SIZE; ++j) {
        ++checked;
        if (output[j] != expected[j]) {
            ++failures;
            std::cerr << "pool nodes=" << nodes << " mode=" << mode
                      << " field=" << j << " expected=" << expected[j]
                      << " actual=" << output[j] << '\n';
        }
    }
}

int main() {
    const int sizes[] = {1, 2, 3, 10, MAX_NODES - 1, MAX_NODES};
    for (int m = 0; m < 3; ++m)
        for (int n : sizes) run_case(n, m);
    run_case(3, 7);
    run_case(1, 2); // Repeated invocation must initialize every output again.
    std::cout << "GNN_FIXTURE fields=" << checked << " failures=" << failures << '\n';
    return failures ? 1 : 0;
}
