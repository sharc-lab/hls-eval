#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "gemver.h"

void init_array(
    int n,
    double *alpha,
    double *beta,
    double A[40][40],
    double u1[40],
    double v1[40],
    double u2[40],
    double v2[40],
    double w[40],
    double x[40],
    double y[40],
    double z[40]) {
    int i, j;

    *alpha = 1.5;
    *beta = 1.2;

    double fn = (double)n;

    for (i = 0; i < n; i++) {
        u1[i] = i;
        u2[i] = ((i + 1) / fn) / 2.0;
        v1[i] = ((i + 1) / fn) / 4.0;
        v2[i] = ((i + 1) / fn) / 6.0;
        y[i] = ((i + 1) / fn) / 8.0;
        z[i] = ((i + 1) / fn) / 9.0;
        x[i] = 0.0;
        w[i] = 0.0;
        for (j = 0; j < n; j++)
            A[i][j] = (double)(i * j % n) / n;
    }
}

void print_array(int n, double w[40]) {
    int i;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "w");
    for (i = 0; i < n; i++) {
        if (i % 20 == 0)
            fprintf(stderr, "\n");
        fprintf(stderr, "%0.6lf ", w[i]);
    }
    fprintf(stderr, "\nend   dump: %s\n", "w");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 40;

    double alpha;
    double beta;
    double A[40][40];
    double u1[40];
    double v1[40];
    double u2[40];
    double v2[40];
    double w[40];
    double x[40];
    double y[40];
    double z[40];

    init_array(n, &alpha, &beta, A, u1, v1, u2, v2, w, x, y, z);

    kernel_gemver(alpha, beta, A, u1, v1, u2, v2, w, x, y, z);

    print_array(n, w);

    return 0;
}