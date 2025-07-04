#include <stdint.h>

/*
Based on algorithm described here:
http://www.cs.berkeley.edu/~mhoemmen/matrix-seminar/slides/UCB_sparse_tutorial_1.pdf
*/

#include <stdio.h>
#include <stdlib.h>

// These constants valid for the IEEE 494 bus interconnect matrix
#define NNZ 1666
#define N 494

#define TYPE double

void spmv(
    TYPE val[NNZ],
    int32_t cols[NNZ],
    int32_t rowDelimiters[N + 1],
    TYPE vec[N],
    TYPE out[N]);
