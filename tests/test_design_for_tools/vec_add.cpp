#include "vec_add.h"

void vec_add(const int in0[VEC_ADD_N], const int in1[VEC_ADD_N], int out[VEC_ADD_N]) {
    for (int i = 0; i < VEC_ADD_N; i++) {
#pragma HLS UNROLL factor = 4
        out[i] = in0[i] + in1[i];
    }
}
