#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "jacobi-2d.h"

void init_array(int n, double A[30][30], double B[30][30]) {
    int i, j;

    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++) {
            A[i][j] = ((double)i * (j + 2) + 2) / n;
            B[i][j] = ((double)i * (j + 3) + 3) / n;
        }
}

void print_array(int n, double A[30][30])

{
    int i, j;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "A");
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++) {
            if ((i * n + j) % 20 == 0)
                fprintf(stderr, "\n");
            fprintf(stderr, "%0.6lf ", A[i][j]);
        }
    fprintf(stderr, "\nend   dump: %s\n", "A");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 30;
    int tsteps = 20;

    double A[30][30];
    double B[30][30];

    init_array(n, A, B);

    kernel_jacobi_2d(A, B);

    print_array(n, A);

    return 0;
}