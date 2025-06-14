#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "bicg.h"

void init_array(int m, int n, double A[42][38], double r[42], double p[38]) {
    int i, j;

    for (i = 0; i < m; i++)
        p[i] = (double)(i % m) / m;
    for (i = 0; i < n; i++) {
        r[i] = (double)(i % n) / n;
        for (j = 0; j < m; j++)
            A[i][j] = (double)(i * (j + 1) % n) / n;
    }
}

void print_array(int m, int n, double s[38], double q[42])

{
    int i;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "s");
    for (i = 0; i < m; i++) {
        if (i % 20 == 0)
            fprintf(stderr, "\n");
        fprintf(stderr, "%0.6lf ", s[i]);
    }
    fprintf(stderr, "\nend   dump: %s\n", "s");
    fprintf(stderr, "begin dump: %s", "q");
    for (i = 0; i < n; i++) {
        if (i % 20 == 0)
            fprintf(stderr, "\n");
        fprintf(stderr, "%0.6lf ", q[i]);
    }
    fprintf(stderr, "\nend   dump: %s\n", "q");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 42;
    int m = 38;

    double A[42][38];
    double s[38];
    double q[42];
    double p[38];
    double r[42];

    init_array(m, n, A, r, p);

    kernel_bicg(A, s, q, p, r);

    print_array(m, n, s, q);

    return 0;
}