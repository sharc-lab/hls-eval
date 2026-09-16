#include <ap_fixed.h>

// -----------------------------------------------------------------------------
// Design-space parameters
// -----------------------------------------------------------------------------

#ifndef SIZE
#define SIZE 32
#endif

#ifndef DATA_T_TOTAL
#define DATA_T_TOTAL 16
#endif

#ifndef DATA_T_INT
#define DATA_T_INT 5
#endif

#ifndef DO_PIPELINE
#define DO_PIPELINE 1
#endif

#ifndef PARALLEL_FACTOR
#define PARALLEL_FACTOR 4
#endif

#ifndef USE_RELU_ACTIVATION
#define USE_RELU_ACTIVATION 0
#endif

// -----------------------------------------------------------------------------
// Derived types
// -----------------------------------------------------------------------------

typedef ap_fixed<DATA_T_TOTAL, DATA_T_INT> data_t;

// -----------------------------------------------------------------------------
// Kernel
// -----------------------------------------------------------------------------

void vec_process(data_t A[SIZE], data_t B[SIZE], data_t C[SIZE]) {

#if PARALLEL_FACTOR > 1
#pragma HLS ARRAY_PARTITION variable = A dim = 1 factor =                      \
    PARALLEL_FACTOR type = cyclic
#pragma HLS ARRAY_PARTITION variable = B dim = 1 factor =                      \
    PARALLEL_FACTOR type = cyclic
#pragma HLS ARRAY_PARTITION variable = C dim = 1 factor =                      \
    PARALLEL_FACTOR type = cyclic
#endif

    for (int i = 0; i < SIZE; i++) {

#if DO_PIPELINE
#pragma HLS PIPELINE II = 1
#endif

#if PARALLEL_FACTOR > 1
#pragma HLS UNROLL factor = PARALLEL_FACTOR
#endif

        data_t result = A[i] + B[i];

#if USE_RELU_ACTIVATION
        C[i] = (result > 0) ? result : data_t(0);
#else
        C[i] = result;
#endif
    }
}
