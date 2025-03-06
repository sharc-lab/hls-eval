#include "ap_fixed.h"

const int MAX_HEIGHT = 436;
const int MAX_WIDTH = 1024;

typedef ap_fixed<17, 9> input_t;
typedef ap_fixed<32, 13> pixel_t;
typedef ap_fixed<32, 27> outer_pixel_t;
typedef ap_fixed<64, 56> calc_pixel_t;
typedef ap_fixed<32, 13> vel_pixel_t;

typedef struct {
    pixel_t x;
    pixel_t y;
    pixel_t z;
} gradient_t;

typedef struct {
    outer_pixel_t val[6];
} outer_t;

typedef struct {
    outer_pixel_t val[6];
} tensor_t;

typedef struct {
    vel_pixel_t x;
    vel_pixel_t y;
} velocity_t;

void gradient_z_calc(
    input_t frame1[MAX_HEIGHT][MAX_WIDTH],
    input_t frame2[MAX_HEIGHT][MAX_WIDTH],
    input_t frame3[MAX_HEIGHT][MAX_WIDTH],
    input_t frame4[MAX_HEIGHT][MAX_WIDTH],
    input_t frame5[MAX_HEIGHT][MAX_WIDTH],
    pixel_t gradient_z[MAX_HEIGHT][MAX_WIDTH]);