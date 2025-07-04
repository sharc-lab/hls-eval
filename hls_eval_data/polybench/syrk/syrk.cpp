#include "syrk.h"

void kernel_syrk(
    double alpha,
    double beta,
    double C[30][30],
    double A[30][20]) {
#pragma HLS top name = kernel_syrk

    const int n = 30;
    const int m = 20;

    int i, j, k;
    for (i = 0; i < n; i++) {
        for (j = 0; j <= i; j++)
            C[i][j] *= beta;
        for (k = 0; k < m; k++) {
            for (j = 0; j <= i; j++)
                C[i][j] += alpha * A[i][k] * A[j][k];
        }
    }
}