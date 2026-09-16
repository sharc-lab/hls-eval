// clang-format off
#include <ap_fixed.h>

// -----------------------------------------------------------------------------
// Derived types
// -----------------------------------------------------------------------------

typedef ap_fixed<24, 8> data_t;

// -----------------------------------------------------------------------------
// Kernel
// -----------------------------------------------------------------------------

void vec_process(data_t A[32], data_t B[32], data_t C[32]) {

#pragma HLS ARRAY_PARTITION variable = A dim = 1 factor = 4 type = cyclic
#pragma HLS ARRAY_PARTITION variable = B dim = 1 factor = 4 type = cyclic
#pragma HLS ARRAY_PARTITION variable = C dim = 1 factor = 4 type = cyclic

    for (int i = 0; i < 32; i++) {

#pragma HLS PIPELINE II = 1

#pragma HLS UNROLL factor = 4

        data_t result = A[i] + B[i];

        C[i] = (result > 0) ? result : data_t(0);

    }
}
// clang-format on