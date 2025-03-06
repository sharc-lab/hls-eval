#include "computeGradient.h"

void computeGradient(
    FeatureType grad[NUM_FEATURES],
    DataType feature[NUM_FEATURES],
    FeatureType scale) {

    const int unroll_factor = PAR_FACTOR;
#pragma HLS array_partition variable = grad cyclic factor = unroll_factor
#pragma HLS array_partition variable = feature cyclic factor = unroll_factor
GRAD:
    for (int i = 0; i < NUM_FEATURES / PAR_FACTOR; i++) {
#pragma HLS PIPELINE II = 1
    GRAD_INNER:
        for (int j = 0; j < PAR_FACTOR; j++) {
            grad[i * PAR_FACTOR + j] = (scale * feature[i * PAR_FACTOR + j]);
        }
    }
}