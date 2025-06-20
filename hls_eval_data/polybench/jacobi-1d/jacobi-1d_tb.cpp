#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "jacobi-1d.h"

void init_array(int n, double A[30], double B[30]) {
    int i;

    for (i = 0; i < n; i++) {
        A[i] = ((double)i + 2) / n;
        B[i] = ((double)i + 3) / n;
    }
}

void print_array(int n, double A[30])

{
    int i;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "A");
    for (i = 0; i < n; i++) {
        if (i % 20 == 0)
            fprintf(stderr, "\n");
        fprintf(stderr, "%0.6lf ", A[i]);
    }
    fprintf(stderr, "\nend   dump: %s\n", "A");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 30;
    int tsteps = 20;

    double A[30];
    double B[30];

    init_array(n, A, B);

    kernel_jacobi_1d(A, B);

    print_array(n, A);

    return 0;
}