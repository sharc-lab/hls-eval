#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ap_fixed.h"
typedef ap_fixed<32, 16> fixed_t;

//-----------------------------------------------
//Original
// #define TILE_ROWS 1024
// #define ROWS 1024
// #define COLS 1024
//-----------------------------------------------
//Alec-added
#define TILE_ROWS 256
#define ROWS 256
#define COLS 256
//-----------------------------------------------
#define R1 0
#define R2 127
#define C1 0
#define C2 127
#define LAMBDA 0.5 
#define PARA_FACTOR 16
#define NITER 2
#define TYPE fixed_t
#define TOP_TILE 0
#define BOTTOM_TILE (ROWS/TILE_ROWS - 1)

fixed_t srad_core1(fixed_t dN, fixed_t dS, fixed_t dW, fixed_t dE,
		  fixed_t Jc, fixed_t q0sqr);
fixed_t srad_core2 (fixed_t dN, fixed_t dS, fixed_t dW, fixed_t dE,
		  fixed_t cN, fixed_t cS, fixed_t cW, fixed_t cE,
		  fixed_t J);
//void srad_kernel1(fixed_t J[(ROWS+3)*COLS], fixed_t q0sqr[1]);
void srad_kernel2(fixed_t J[(TILE_ROWS+3)*COLS], fixed_t Jout[TILE_ROWS*COLS], fixed_t q0sqr, int tile);

////////////////////////////////////////////////////////////////////////////////
// Test harness interface code.

struct bench_args_t {
  fixed_t J[(ROWS+3)*COLS];
  fixed_t Jout[(ROWS+3)*COLS];
};
