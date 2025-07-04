#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "trisolv.h"

void init_array(int n, double L[40][40], double x[40], double b[40]) {
    int i, j;

    for (i = 0; i < n; i++) {
        x[i] = -999;
        b[i] = i;
        for (j = 0; j <= i; j++)
            L[i][j] = (double)(i + n - j + 1) * 2 / n;
    }
}

void print_array(int n, double x[40])

{
    int i;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "x");
    for (i = 0; i < n; i++) {
        fprintf(stderr, "%0.6lf ", x[i]);
        if (i % 20 == 0)
            fprintf(stderr, "\n");
    }
    fprintf(stderr, "\nend   dump: %s\n", "x");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 40;

    double L[40][40];
    double x[40];
    double b[40];

    init_array(n, L, x, b);

    kernel_trisolv(L, x, b);

    print_array(n, x);

    return 0;
}