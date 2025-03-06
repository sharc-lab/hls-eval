#include "outer_product.h"

void outer_product(
    gradient_t gradient[MAX_HEIGHT][MAX_WIDTH],
    outer_t outer_product[MAX_HEIGHT][MAX_WIDTH]) {
OUTER_OUTER:
    for (int r = 0; r < MAX_HEIGHT; r++) {
    OUTER_INNER:
        for (int c = 0; c < MAX_WIDTH; c++) {
            gradient_t grad = gradient[r][c];
            outer_pixel_t x = (outer_pixel_t)grad.x;
            outer_pixel_t y = (outer_pixel_t)grad.y;
            outer_pixel_t z = (outer_pixel_t)grad.z;
            outer_t out;
            out.val[0] = (x * x);
            out.val[1] = (y * y);
            out.val[2] = (z * z);
            out.val[3] = (x * y);
            out.val[4] = (x * z);
            out.val[5] = (y * z);
            outer_product[r][c] = out;
        }
    }
}