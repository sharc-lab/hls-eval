#include "YuvToRgb.h"

/*
 * Transform from Yuv into RGB
 */
void YuvToRgb(
    int p,
    int y_buf[DCTSIZE2],
    int u_buf[DCTSIZE2],
    int v_buf[DCTSIZE2],
    int rgb_buf[4][RGB_NUM][DCTSIZE2]) {
    int r, g, b;
    int y, u, v;
    int i;

    for (i = 0; i < DCTSIZE2; i++) {
        y = y_buf[i];
        u = u_buf[i] - 128;
        v = v_buf[i] - 128;

        r = (y * 256 + v * 359 + 128) >> 8;
        g = (y * 256 - u * 88 - v * 182 + 128) >> 8;
        b = (y * 256 + u * 454 + 128) >> 8;

        if (r < 0)
            r = 0;
        else if (r > 255)
            r = 255;

        if (g < 0)
            g = 0;
        else if (g > 255)
            g = 255;

        if (b < 0)
            b = 0;
        else if (b > 255)
            b = 255;

        rgb_buf[p][0][i] = r;
        rgb_buf[p][1][i] = g;
        rgb_buf[p][2][i] = b;
    }
}