#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvt.h"

void init_array(
    int n,
    double x1[40],
    double x2[40],
    double y_1[40],
    double y_2[40],
    double A[40][40]) {
    int i, j;

    for (i = 0; i < n; i++) {
        x1[i] = (double)(i % n) / n;
        x2[i] = (double)((i + 1) % n) / n;
        y_1[i] = (double)((i + 3) % n) / n;
        y_2[i] = (double)((i + 4) % n) / n;
        for (j = 0; j < n; j++)
            A[i][j] = (double)(i * j % n) / n;
    }
}

void print_array(int n, double x1[40], double x2[40])

{
    int i;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "x1");
    for (i = 0; i < n; i++) {
        if (i % 20 == 0)
            fprintf(stderr, "\n");
        fprintf(stderr, "%0.6lf ", x1[i]);
    }
    fprintf(stderr, "\nend   dump: %s\n", "x1");

    fprintf(stderr, "begin dump: %s", "x2");
    for (i = 0; i < n; i++) {
        if (i % 20 == 0)
            fprintf(stderr, "\n");
        fprintf(stderr, "%0.6lf ", x2[i]);
    }
    fprintf(stderr, "\nend   dump: %s\n", "x2");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 40;

    double A[40][40];
    double x1[40];
    double x2[40];
    double y_1[40];
    double y_2[40];

    init_array(n, x1, x2, y_1, y_2, A);

    kernel_mvt(x1, x2, y_1, y_2, A);

    print_array(n, x1, x2);

    return 0;
}