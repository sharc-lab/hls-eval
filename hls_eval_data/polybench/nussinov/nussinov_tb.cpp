#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nussinov.h"

void init_array(int n, char seq[60], int table[60][60]) {
    int i, j;

    for (i = 0; i < n; i++) {
        seq[i] = (char)((i + 1) % 4);
    }

    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++)
            table[i][j] = 0;
}

void print_array(int n, int table[60][60])

{
    int i, j;
    int t = 0;

    fprintf(stderr, "==BEGIN DUMP_ARRAYS==\n");
    fprintf(stderr, "begin dump: %s", "table");
    for (i = 0; i < n; i++) {
        for (j = i; j < n; j++) {
            if (t % 20 == 0)
                fprintf(stderr, "\n");
            fprintf(stderr, "%d ", table[i][j]);
            t++;
        }
    }
    fprintf(stderr, "\nend   dump: %s\n", "table");
    fprintf(stderr, "==END   DUMP_ARRAYS==\n");
}

int main() {

    int n = 60;

    char seq[60];
    int table[60][60];

    init_array(n, seq, table);

    kernel_nussinov(seq, table);

    print_array(n, table);

    return 0;
}