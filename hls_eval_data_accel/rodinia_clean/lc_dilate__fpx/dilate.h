#ifndef LC_DILATE_H
#define LC_DILATE_H

#include <iostream>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "ap_fixed.h"
typedef ap_fixed<48, 24> fixed_t;

#define GRID_ROWS 544//2048
#define GRID_COLS 512

#define TILE_ROWS 32
#define TILE_COLS 128 // array partition limits the number of bram to be less than 1024

//#define PARA_FACTOR 32

#define STREL_ROWS 5
#define STREL_COLS 5

#define MAX_RADIUS 2

#define PI 3.1415926
#define TOP 0
#define BOTTOM (GRID_ROWS / TILE_ROWS - 1)

#define TYPE fixed_t

struct bench_args_t{
	fixed_t result[GRID_ROWS * GRID_COLS]; 
	fixed_t img[(GRID_ROWS+2*MAX_RADIUS)*GRID_COLS];
};

#endif