#include "linear.h"

void linear_output_stationary(
    FM_TYPE input[DIM_IN],
    WT_TYPE weight[DIM_OUT][DIM_IN],
    WT_TYPE bias[DIM_OUT],
    hls::stream<array<FM_TYPE, PARALLEL>> &output) {
#pragma HLS INLINE off
#pragma HLS ARRAY_PARTITION variable = input complete dim = 1
#pragma HLS ARRAY_PARTITION variable = weight cyclic factor = PARALLEL dim = 1
#pragma HLS ARRAY_PARTITION variable = weight complete dim = 2
#pragma HLS ARRAY_PARTITION variable = bias cyclic factor = PARALLEL dim = 1

    for (int dim_out_base = 0; dim_out_base < DIM_OUT;
         dim_out_base += PARALLEL) {
#pragma HLS PIPELINE II = 1
        array<FM_TYPE, PARALLEL> out_slice;
        for (int dim_out_offset = 0; dim_out_offset < PARALLEL;
             dim_out_offset++) {
#pragma HLS UNROLL
            int dim_out = dim_out_base + dim_out_offset;
            FM_TYPE out_el = 0;

            if (dim_out < DIM_OUT) {
                out_el = bias[dim_out];
                for (int dim_in = 0; dim_in < DIM_IN; dim_in++) {
#pragma HLS UNROLL
                    out_el += input[dim_in] * weight[dim_out][dim_in];
                }
            }

            if (RELU && out_el < 0)
                out_el = 0;
            out_slice[dim_out_offset] = out_el;
        }
        output << out_slice;
    }
}