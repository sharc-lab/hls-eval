#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "floyd-warshall.h"

void init_array(int n, int path[60][60]) {
    int i, j;

    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++) {
            path[i][j] = i * j % 7 + 1;
            if ((i + j) % 13 == 0 || (i + j) % 7 == 0 || (i + j) % 11 == 0)
                path[i][j] = 999;
        }
}

void print_array(int n, int path[60][60])

{
    int i, j;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "path");
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++) {
            if ((i * n + j) % 20 == 0)
                fprintf(stderr, "\n");
            fprintf(stderr, "%d ", path[i][j]);
        }
    fprintf(stderr, "\nend   dump: %s\n", "path");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 60;

    int path[60][60];

    init_array(n, path);

    kernel_floyd_warshall(path);

    print_array(n, path);

    return 0;
}