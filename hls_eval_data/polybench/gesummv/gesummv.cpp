#include "gesummv.h"

void kernel_gesummv(
    double alpha,
    double beta,
    double A[30][30],
    double B[30][30],
    double tmp[30],
    double x[30],
    double y[30]) {
#pragma HLS top name = kernel_gesummv

    const int n = 30;

    int i, j;

    for (i = 0; i < n; i++) {
        tmp[i] = 0.0;
        y[i] = 0.0;
        for (j = 0; j < n; j++) {
            tmp[i] = A[i][j] * x[j] + tmp[i];
            y[i] = B[i][j] * x[j] + y[i];
        }
        y[i] = alpha * tmp[i] + beta * y[i];
    }
}