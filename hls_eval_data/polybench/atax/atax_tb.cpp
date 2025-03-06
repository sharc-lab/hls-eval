#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "atax.h"

void init_array(int m, int n, double A[38][42], double x[42]) {
    int i, j;
    double fn;
    fn = (double)n;

    for (i = 0; i < n; i++)
        x[i] = 1 + (i / fn);
    for (i = 0; i < m; i++)
        for (j = 0; j < n; j++)
            A[i][j] = (double)((i + j) % n) / (5 * m);
}

void print_array(int n, double y[42])

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

    int m = 38;
    int n = 42;

    double A[38][42];
    double x[42];
    double y[42];
    double tmp[38];

    init_array(m, n, A, x);

    kernel_atax(A, x, y, tmp);

    print_array(n, y);

    return 0;
}