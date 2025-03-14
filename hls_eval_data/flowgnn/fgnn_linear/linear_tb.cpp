#include "linear.h"

int main() {
    FM_TYPE input[DIM_IN];
    WT_TYPE weight[DIM_OUT][DIM_IN];
    WT_TYPE bias[DIM_OUT];
    FM_TYPE output[DIM_OUT];

    for (int i = 0; i < DIM_IN; i++) {
        input[i] = DIM_IN - 2 * FM_TYPE(i);
    }

    for (int i = 0; i < DIM_OUT; i++) {
        bias[i] = -WT_TYPE(i) / DIM_OUT;
        for (int j = 0; j < DIM_IN; j++) {
            weight[i][j] = WT_TYPE(i + j) / (DIM_OUT * DIM_IN);
        }
    }

    linear(input, weight, bias, output);

    for (int i = 0; i < DIM_OUT; i++) {
        printf("%f\n", output[i]);
    }

    return 0;
}