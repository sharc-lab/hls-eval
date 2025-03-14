#include "linear.h"

void linear_input_stationary(
    hls::stream<array<FM_TYPE, PARALLEL>> &input,
    WT_TYPE weight[DIM_OUT][DIM_IN],
    WT_TYPE bias[DIM_OUT],
    FM_TYPE output[DIM_OUT]) {
#pragma HLS INLINE off
#pragma HLS ARRAY_PARTITION variable = weight complete dim = 1
#pragma HLS ARRAY_PARTITION variable = weight cyclic factor = PARALLEL dim = 2
#pragma HLS ARRAY_PARTITION variable = bias complete dim = 1
#pragma HLS ARRAY_PARTITION variable = output complete dim = 1

    for (int dim_out = 0; dim_out < DIM_OUT; dim_out++) {
#pragma HLS UNROLL
        output[dim_out] = bias[dim_out];
    }

    for (int dim_in_base = 0; dim_in_base < DIM_IN; dim_in_base += PARALLEL) {
#pragma HLS PIPELINE II = 1
        array<FM_TYPE, PARALLEL> in_slice;
        input >> in_slice;
        for (int dim_out = 0; dim_out < DIM_OUT; dim_out++) {
#pragma HLS UNROLL
            FM_TYPE addend = 0;
            for (int dim_in_offset = 0; dim_in_offset < PARALLEL;
                 dim_in_offset++) {
#pragma HLS UNROLL
                int dim_in = dim_in_base + dim_in_offset;
                FM_TYPE in_el = in_slice[dim_in_offset];
                if (dim_in < DIM_IN) {
                    addend += in_el * weight[dim_out][dim_in];
                }
            }
            output[dim_out] += addend;
        }
    }

    for (int dim_out = 0; dim_out < DIM_OUT; dim_out++) {
#pragma HLS UNROLL
        if (RELU && output[dim_out] < 0)
            output[dim_out] = 0;
    }
}