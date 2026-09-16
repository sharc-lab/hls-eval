// clang-format off
#include <ap_fixed.h>

// -----------------------------------------------------------------------------
// Derived types
// -----------------------------------------------------------------------------

typedef ap_fixed<32, 12> data_t;

// -----------------------------------------------------------------------------
// Kernel
// -----------------------------------------------------------------------------

void vec_process(data_t A[64], data_t B[64], data_t C[64]) {

#pragma HLS ARRAY_PARTITION variable = A dim = 1 factor = 8 type = cyclic
#pragma HLS ARRAY_PARTITION variable = B dim = 1 factor = 8 type = cyclic
#pragma HLS ARRAY_PARTITION variable = C dim = 1 factor = 8 type = cyclic

    for (int i = 0; i < 64; i++) {

#pragma HLS UNROLL factor = 8

        data_t result = A[i] + B[i];

        C[i] = (result > 0) ? result : data_t(0);

    }
}
// clang-format on