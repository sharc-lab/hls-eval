#define RGB_NUM 3
#define DCTSIZE2 64

void YuvToRgb(
    int p,
    int y_buf[DCTSIZE2],
    int u_buf[DCTSIZE2],
    int v_buf[DCTSIZE2],
    int rgb_buf[4][RGB_NUM][DCTSIZE2]);