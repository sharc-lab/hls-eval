#include "2mm.h"

void kernel_2mm(
    double alpha,
    double beta,
    double tmp[16][18],
    double A[16][22],
    double B[22][18],
    double C[18][24],
    double D[16][24]) {
#pragma HLS top name = kernel_2mm

    const int ni = 16;
    const int nj = 18;
    const int nk = 22;
    const int nl = 24;

    int i, j, k;

    for (i = 0; i < ni; i++)
        for (j = 0; j < nj; j++) {
            tmp[i][j] = 0.0;
            for (k = 0; k < nk; ++k)
                tmp[i][j] += alpha * A[i][k] * B[k][j];
        }
    for (i = 0; i < ni; i++)
        for (j = 0; j < nl; j++) {
            D[i][j] *= beta;
            for (k = 0; k < nj; ++k)
                D[i][j] += tmp[i][k] * C[k][j];
        }
}