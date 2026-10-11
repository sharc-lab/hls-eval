#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "gramschmidt.h"

void init_array(
    int m,
    int n,
    double A[20][30],
    double R[30][30],
    double Q[20][30]) {
    int i, j;

    for (i = 0; i < m; i++)
        for (j = 0; j < n; j++) {
            A[i][j] = (i == (j % m) ? 1.0 : 0.0);
            Q[i][j] = 0.0;
        }
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++)
            R[i][j] = 0.0;
}

void print_array(
    int m,
    int n,
    double A[20][30],
    double R[30][30],
    double Q[20][30]) {
    int i, j;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "R");
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++) {
            if ((i * n + j) % 20 == 0)
                fprintf(stderr, "\n");
            fprintf(stderr, "%.17g ", R[i][j]);
        }
    fprintf(stderr, "\nend   dump: %s\n", "R");

    fprintf(stderr, "begin dump: %s", "Q");
    for (i = 0; i < m; i++)
        for (j = 0; j < n; j++) {
            if ((i * n + j) % 20 == 0)
                fprintf(stderr, "\n");
            fprintf(stderr, "%.17g ", Q[i][j]);
        }
    fprintf(stderr, "\nend   dump: %s\n", "Q");
    fprintf(stderr, "begin dump: A\n");
  for (int ai = 0; ai < m; ++ai) {
    for (int aj = 0; aj < n; ++aj)
      fprintf(stderr, "%.17g ", A[ai][aj]);
    fprintf(stderr, "\n");
  }
  fprintf(stderr, "end   dump: A\n");
  fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int m = 20;
    int n = 30;

    double A[20][30];
    double R[30][30];
    double Q[20][30];

    init_array(m, n, A, R, Q);

    kernel_gramschmidt(A, R, Q);

    print_array(m, n, A, R, Q);

    return 0;
}