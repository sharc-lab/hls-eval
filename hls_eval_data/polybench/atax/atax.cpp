#include "atax.h"

void kernel_atax(double A[38][42], double x[42], double y[42], double tmp[38]) {
#pragma HLS top name = kernel_atax

    const int m = 38;
    const int n = 42;

    int i, j;

    for (i = 0; i < n; i++)
        y[i] = 0;
    for (i = 0; i < m; i++) {
        tmp[i] = 0.0;
        for (j = 0; j < n; j++)
            tmp[i] = tmp[i] + A[i][j] * x[j];
        for (j = 0; j < n; j++)
            y[j] = y[j] + A[i][j] * tmp[i];
    }
}