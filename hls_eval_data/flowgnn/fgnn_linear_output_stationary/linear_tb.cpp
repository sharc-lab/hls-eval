#include "linear.h"

int main() {
    FM_TYPE input[DIM_IN];
    WT_TYPE weight[DIM_OUT][DIM_IN];
    WT_TYPE bias[DIM_OUT];
    FM_TYPE output[DIM_OUT] = {0};

    for (int i = 0; i < DIM_IN; i++) {
        input[i] = DIM_IN - 2 * FM_TYPE(i);
    }

    for (int i = 0; i < DIM_OUT; i++) {
        bias[i] = -WT_TYPE(i) / DIM_OUT;
        for (int j = 0; j < DIM_IN; j++) {
            weight[i][j] = WT_TYPE(i + j) / (DIM_OUT * DIM_IN);
        }
    }

    hls::stream<std::array<FM_TYPE, PARALLEL>> output_stream;

    linear_output_stationary(input, weight, bias, output_stream);

    // buffer out the output stream
    for (int i = 0; i < DIM_OUT; i += PARALLEL) {
        std::array<FM_TYPE, PARALLEL> out_slice;
        output_stream.read(out_slice);
        for (int j = 0; j < PARALLEL; j++) {
            if (i + j < DIM_OUT)
                output[i + j] = out_slice[j];
        }
    }

    return 0;
}