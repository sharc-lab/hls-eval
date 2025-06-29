#include <stdint.h>

#include <stdio.h>
#include <stdlib.h>

// Define input sizes
#define col_size 64
#define row_size 128
#define f_size 9

// Data Bounds
#define TYPE int32_t
#define MAX 1000
#define MIN 1

// Set number of iterations to execute
#define MAX_ITERATION 1

void stencil(
    TYPE orig[row_size * col_size],
    TYPE sol[row_size * col_size],
    TYPE filter[f_size]);
