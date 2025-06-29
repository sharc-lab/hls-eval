#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "doitgen.h"

void init_array(
    int nr,
    int nq,
    int np,
    double A[10][8][12],
    double C4[12][12]) {
    int i, j, k;

    for (i = 0; i < nr; i++)
        for (j = 0; j < nq; j++)
            for (k = 0; k < np; k++)
                A[i][j][k] = (double)((i * j + k) % np) / np;
    for (i = 0; i < np; i++)
        for (j = 0; j < np; j++)
            C4[i][j] = (double)(i * j % np) / np;
}

void print_array(int nr, int nq, int np, double A[10][8][12]) {
    int i, j, k;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "A");
    for (i = 0; i < nr; i++)
        for (j = 0; j < nq; j++)
            for (k = 0; k < np; k++) {
                if ((i * nq * np + j * np + k) % 20 == 0)
                    fprintf(stderr, "\n");
                fprintf(stderr, "%0.6lf ", A[i][j][k]);
            }
    fprintf(stderr, "\nend   dump: %s\n", "A");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int nr = 10;
    int nq = 8;
    int np = 12;

    double A[10][8][12];
    double sum[12];
    double C4[12][12];

    init_array(nr, nq, np, A, C4);

    kernel_doitgen(A, C4, sum);

    print_array(nr, nq, np, A);

    return 0;
}