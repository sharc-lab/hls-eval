#include "flow_calc.h"

void flow_calc(
    tensor_t tensors[MAX_HEIGHT][MAX_WIDTH],
    velocity_t outputs[MAX_HEIGHT][MAX_WIDTH]) {
    static outer_pixel_t buf[2];
FLOW_OUTER:
    for (int r = 0; r < MAX_HEIGHT; r++) {
    FLOW_INNER:
        for (int c = 0; c < MAX_WIDTH; c++) {
            tensor_t tmp_tensor = tensors[r][c];
            if (r >= 2 && r < MAX_HEIGHT - 2 && c >= 2 && c < MAX_WIDTH - 2) {
                calc_pixel_t t1 = (calc_pixel_t)tmp_tensor.val[0];
                calc_pixel_t t2 = (calc_pixel_t)tmp_tensor.val[1];
                calc_pixel_t t3 = (calc_pixel_t)tmp_tensor.val[2];
                calc_pixel_t t4 = (calc_pixel_t)tmp_tensor.val[3];
                calc_pixel_t t5 = (calc_pixel_t)tmp_tensor.val[4];
                calc_pixel_t t6 = (calc_pixel_t)tmp_tensor.val[5];

                calc_pixel_t denom = t1 * t2 - t4 * t4;
                calc_pixel_t numer0 = t6 * t4 - t5 * t2;
                calc_pixel_t numer1 = t5 * t4 - t6 * t1;

                if (denom != 0) {
                    buf[0] = numer0 / denom;
                    buf[1] = numer1 / denom;
                } else {
                    buf[0] = 0;
                    buf[1] = 0;
                }
            } else {
                buf[0] = buf[1] = 0;
            }

            outputs[r][c].x = (vel_pixel_t)buf[0];
            outputs[r][c].y = (vel_pixel_t)buf[1];
        }
    }
}