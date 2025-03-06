#include "dotProduct.h"

FeatureType
dotProduct(FeatureType param[NUM_FEATURES], DataType feature[NUM_FEATURES]) {
    const int unroll_factor = PAR_FACTOR;

#pragma HLS array_partition variable = param cyclic factor = unroll_factor
#pragma HLS array_partition variable = feature cyclic factor = unroll_factor

    FeatureType result = 0;
DOT:
    for (int i = 0; i < NUM_FEATURES / PAR_FACTOR; i++) {
#pragma HLS PIPELINE II = 1
    DOT_INNER:
        for (int j = 0; j < PAR_FACTOR; j++) {
            FeatureType term =
                param[i * PAR_FACTOR + j] * feature[i * PAR_FACTOR + j];
            result += term;
        }
    }
    return result;
}
