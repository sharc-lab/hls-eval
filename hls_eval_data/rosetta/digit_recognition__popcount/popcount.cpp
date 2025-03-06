#include "popcount.h"

int popcount(WholeDigitType x) {
    // most straightforward implementation
    // actually not bad on FPGA
    int cnt = 0;
    for (int i = 0; i < 256; i++)
        cnt = cnt + x[i];

    return cnt;
}