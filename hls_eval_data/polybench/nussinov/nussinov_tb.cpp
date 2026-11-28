#include "nussinov.h"
#include <algorithm>
#include <iostream>

// Independent oracle: either the leftmost base is unpaired, or enumerate its
// partner and combine the disjoint inside/right matchings. No DUT/reference call.
static int memo[60][60];
static int score(const char seq[60], int i, int j) {
    if (i >= j) return 0;
    if (memo[i][j] >= 0) return memo[i][j];
    int best = score(seq, i + 1, j);
    for (int p = i + 1; p <= j; ++p) {
        bool pair = (seq[i] == 'A' && (seq[p] == 'T' || seq[p] == 'U')) ||
                    (seq[p] == 'A' && (seq[i] == 'T' || seq[i] == 'U')) ||
                    (seq[i] == 'G' && seq[p] == 'C') ||
                    (seq[i] == 'C' && seq[p] == 'G');
        if (pair) best = std::max(best, 1 + score(seq, i + 1, p - 1)
                                        + score(seq, p + 1, j));
    }
    return memo[i][j] = best;
}

int main() {
    const char *patterns[] = {"A", "GC", "AU", "AT", "AGCTU", "UGAACGTTAC"};
    const int lengths[] = {1, 2, 2, 2, 5, 10};
    int fields = 0, failures = 0;
    for (int c = 0; c < 6; ++c) {
        char seq[60], original_seq[60];
        int table[60][60];
        for (int i = 0; i < 60; ++i) {
            seq[i] = patterns[c][i % lengths[c]];
            original_seq[i] = seq[i];
            for (int j = 0; j < 60; ++j) {
                table[i][j] = -777;
                memo[i][j] = -1;
            }
        }
        kernel_nussinov(seq, table);
        for (int i = 0; i < 60; ++i) {
            if (seq[i] != original_seq[i]) ++failures;
            for (int j = i; j < 60; ++j) {
                ++fields;
                int expected = score(original_seq, i, j);
                if (table[i][j] != expected) {
                    if (failures < 8) std::cerr << "case=" << c << " field=" << i
                        << ',' << j << " expected=" << expected
                        << " actual=" << table[i][j] << '\n';
                    ++failures;
                }
            }
        }
    }
    std::cout << "NUSSINOV_FIXTURE fields=" << fields << " failures=" << failures << '\n';
    return failures ? 1 : 0;
}
