#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "gesummv.h"

void init_array(
    int n,
    double *alpha,
    double *beta,
    double A[30][30],
    double B[30][30],
    double x[30]) {
    int i, j;

    *alpha = 1.5;
    *beta = 1.2;
    for (i = 0; i < n; i++) {
        x[i] = (double)(i % n) / n;
        for (j = 0; j < n; j++) {
            A[i][j] = (double)((i * j + 1) % n) / n;
            B[i][j] = (double)((i * j + 2) % n) / n;
        }
    }
}

void print_array(int n, double y[30])

{
    int i;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "y");
    for (i = 0; i < n; i++) {
        if (i % 20 == 0)
            fprintf(stderr, "\n");
        fprintf(stderr, "%0.6lf ", y[i]);
    }
    fprintf(stderr, "\nend   dump: %s\n", "y");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 30;

    double alpha;
    double beta;
    double A[30][30];
    double B[30][30];
    double tmp[30];
    double x[30];
    double y[30];

    init_array(n, &alpha, &beta, A, B, x);

    kernel_gesummv(alpha, beta, A, B, tmp, x, y);

    print_array(n, y);

    return 0;
}