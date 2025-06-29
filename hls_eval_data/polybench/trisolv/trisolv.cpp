#include "trisolv.h"

void kernel_trisolv(double L[40][40], double x[40], double b[40]) {
#pragma HLS top name = kernel_trisolv

    const int n = 40;

    int i, j;

    for (i = 0; i < n; i++) {
        x[i] = b[i];
        for (j = 0; j < i; j++)
            x[i] -= L[i][j] * x[j];
        x[i] = x[i] / L[i][i];
    }
}