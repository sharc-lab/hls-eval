#include <cstdio>
#include "linear.h"

int main() {
    FM_TYPE input[DIM_IN];
    WT_TYPE weight[DIM_OUT][DIM_IN];
    WT_TYPE bias[DIM_OUT];
    FM_TYPE output[DIM_OUT] = {0};

    for (int i = 0; i < DIM_IN; i++) {
        input[i] = FM_TYPE(1) + FM_TYPE(i % 4) / 4;
    }

    for (int i = 0; i < DIM_OUT; i++) {
        bias[i] = -WT_TYPE(i) / DIM_OUT;
        for (int j = 0; j < DIM_IN; j++) {
            weight[i][j] = WT_TYPE(i % 2 == 0 ? 1 : -1) / DIM_IN;
        }
    }

    FM_TYPE expected[DIM_OUT];
    for (int i = 0; i < DIM_OUT; ++i) {
        expected[i] = bias[i];
        for (int j = 0; j < DIM_IN; ++j) expected[i] += input[j] * weight[i][j];
        if (RELU && expected[i] < 0) expected[i] = 0;
    }
    hls::stream<std::array<FM_TYPE, PARALLEL>> output_stream;

    linear_output_stationary(input, weight, bias, output_stream);

    // buffer out the output stream
    for (int i = 0; i < DIM_OUT; i += PARALLEL) {
        std::array<FM_TYPE, PARALLEL> out_slice;
        if (output_stream.empty()) return 1;
        output_stream.read(out_slice);
        for (int j = 0; j < PARALLEL; j++) {
            if (i + j < DIM_OUT)
                output[i + j] = out_slice[j];
        }
    }

    if (!output_stream.empty()) return 1;
    for (int i = 0; i < DIM_OUT; ++i)
        if (output[i] != expected[i]) return 1;
    std::printf("LINEAR fields=%d failures=0\n", DIM_OUT);
    return 0;
}