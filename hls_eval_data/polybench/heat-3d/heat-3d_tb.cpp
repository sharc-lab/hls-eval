#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "heat-3d.h"

void init_array(int n, double A[10][10][10], double B[10][10][10]) {
    int i, j, k;

    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++)
            for (k = 0; k < n; k++)
                A[i][j][k] = B[i][j][k] = (double)((i*i + 3*j + 2*k*k + i*j + 1) % 113) / 128.0;
}

void print_array(int n, double A[10][10][10], const char *label)

{
    int i, j, k;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", label);
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++)
            for (k = 0; k < n; k++) {
                if ((i * n * n + j * n + k) % 20 == 0)
                    fprintf(stderr, "\n");
                fprintf(stderr, "%.17g ", A[i][j][k]);
            }
    fprintf(stderr, "\nend   dump: %s\n", label);
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 10;
    int tsteps = 20;

    double A[10][10][10];
    double B[10][10][10];

    init_array(n, A, B);

    kernel_heat_3d(A, B);

    print_array(n, A, "A");
    print_array(n, B, "B");

    return 0;
}