#ifndef LUD_H
#define LUD_H

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "ap_fixed.h"
typedef ap_fixed<32, 16> fixed_t;


#define GRID_ROWS 256
#define GRID_COLS 256
#define SIZE GRID_ROWS
#define TILE_ROWS 4
#define PARA_FACTOR 8
#define TOP 0
#define BOTTOM (GRID_ROWS / TILE_ROWS - 1)

#define TYPE fixed_t

struct bench_args_t {
    fixed_t result[GRID_ROWS * GRID_COLS];
};

// void workload(fixed_t result[GRID_ROWS * GRID_COLS]);
#endif
