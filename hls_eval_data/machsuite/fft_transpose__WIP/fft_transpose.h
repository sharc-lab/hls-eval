#include <stdint.h>

/*
Implementations based on:
V. Volkov and B. Kazian. Fitting fft onto the g80 architecture. 2008.
*/

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define TYPE double

typedef struct complex_t {
    TYPE x;
    TYPE y;
} complex;

#define PI 3.1415926535
#ifndef M_SQRT1_2
#define M_SQRT1_2 0.70710678118654752440f
#endif
void fft1D_512(TYPE work_x[512], TYPE work_y[512]);
