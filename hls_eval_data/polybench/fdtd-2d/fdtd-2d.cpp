#include "fdtd-2d.h"

void kernel_fdtd_2d(

    double ex[20][30],
    double ey[20][30],
    double hz[20][30],
    double _fict_[20]) {
#pragma HLS top name = kernel_fdtd_2d

    const int tmax = 20;
    const int nx = 20;
    const int ny = 30;

    int t, i, j;

    for (t = 0; t < tmax; t++) {
        for (j = 0; j < ny; j++)
            ey[0][j] = _fict_[t];
        for (i = 1; i < nx; i++)
            for (j = 0; j < ny; j++)
                ey[i][j] = ey[i][j] - 0.5 * (hz[i][j] - hz[i - 1][j]);
        for (i = 0; i < nx; i++)
            for (j = 1; j < ny; j++)
                ex[i][j] = ex[i][j] - 0.5 * (hz[i][j] - hz[i][j - 1]);
        for (i = 0; i < nx - 1; i++)
            for (j = 0; j < ny - 1; j++)
                hz[i][j] = hz[i][j] - 0.7 * (ex[i][j + 1] - ex[i][j] +
                                             ey[i + 1][j] - ey[i][j]);
    }
}