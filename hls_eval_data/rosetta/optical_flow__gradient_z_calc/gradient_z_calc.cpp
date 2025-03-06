#include "gradient_z_calc.h"

void gradient_z_calc(
    input_t frame1[MAX_HEIGHT][MAX_WIDTH],
    input_t frame2[MAX_HEIGHT][MAX_WIDTH],
    input_t frame3[MAX_HEIGHT][MAX_WIDTH],
    input_t frame4[MAX_HEIGHT][MAX_WIDTH],
    input_t frame5[MAX_HEIGHT][MAX_WIDTH],
    pixel_t gradient_z[MAX_HEIGHT][MAX_WIDTH]) {
    const int GRAD_WEIGHTS[] = {1, -8, 0, 8, -1};
GRAD_Z_OUTER:
    for (int r = 0; r < MAX_HEIGHT; r++) {
    GRAD_Z_INNER:
        for (int c = 0; c < MAX_WIDTH; c++) {
            gradient_z[r][c] = ((pixel_t)(frame1[r][c] * GRAD_WEIGHTS[0] +
                                          frame2[r][c] * GRAD_WEIGHTS[1] +
                                          frame3[r][c] * GRAD_WEIGHTS[2] +
                                          frame4[r][c] * GRAD_WEIGHTS[3] +
                                          frame5[r][c] * GRAD_WEIGHTS[4])) /
                               12;
        }
    }
}