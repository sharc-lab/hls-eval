#include "nussinov.h"

static int complementary(char a, char b) {
    return (a == 'A' && (b == 'T' || b == 'U')) ||
           (b == 'A' && (a == 'T' || a == 'U')) ||
           (a == 'G' && b == 'C') || (a == 'C' && b == 'G');
}

void kernel_nussinov(char seq[60], int table[60][60]) {
#pragma HLS top name = kernel_nussinov
    for (int i = 0; i < 60; ++i) table[i][i] = 0;
    for (int length = 2; length <= 60; ++length) {
        for (int i = 0; i + length <= 60; ++i) {
            int j = i + length - 1;
            int best = table[i + 1][j];
            if (table[i][j - 1] > best) best = table[i][j - 1];
            int pair = (length > 2 ? table[i + 1][j - 1] : 0)
                       + complementary(seq[i], seq[j]);
            if (pair > best) best = pair;
            for (int k = i + 1; k < j; ++k) {
                int split = table[i][k] + table[k + 1][j];
                if (split > best) best = split;
            }
            table[i][j] = best;
        }
    }
}
