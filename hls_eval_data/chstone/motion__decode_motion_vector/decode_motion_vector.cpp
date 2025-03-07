#include "decode_motion_vector.h"

void decode_motion_vector(
    int *pred,
    int r_size,
    int motion_code,
    int motion_residual,
    int full_pel_vector) {
    int lim, vec;

    r_size = r_size % 32;
    lim = 16 << r_size;
    vec = full_pel_vector ? (*pred >> 1) : (*pred);

    if (motion_code > 0) {
        vec += ((motion_code - 1) << r_size) + motion_residual + 1;
        if (vec >= lim)
            vec -= lim + lim;
    } else if (motion_code < 0) {
        vec -= ((-motion_code - 1) << r_size) + motion_residual + 1;
        if (vec < -lim)
            vec += lim + lim;
    }
    *pred = full_pel_vector ? (vec << 1) : vec;
}
