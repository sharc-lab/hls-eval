#ifndef LC_GICOV_H
#define LC_GICOV_H

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "ap_fixed.h"

typedef ap_fixed<64, 48> fixed_t;

#define GRID_ROWS 256
#define GRID_COLS 256

#define TILE_ROWS 64

#define PARA_FACTOR 4


// The number of sample points per ellipse
#define NPOINTS 16
// The expected radius (in pixels) of a cell
#define MIN_RADIUS 2
// The number of different sample ellipses to try
#define NCIRCLES 2
// Stride
#define STRIDE 1

#define MAX_RADIUS (MIN_RADIUS + STRIDE * (NCIRCLES - 1))

#define PI 3.1415926

#define TOP 0
#define BOTTOM (GRID_ROWS / TILE_ROWS - 1)


#define TYPE fixed_t

struct bench_args_t {
    fixed_t result[GRID_ROWS * GRID_COLS];
    fixed_t grad_x[GRID_ROWS * GRID_COLS];
    fixed_t grad_y[GRID_ROWS * GRID_COLS];
};

#endif
