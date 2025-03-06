#include "ap_int.h"
typedef ap_uint<256> WholeDigitType;

// parameters
#define K_CONST 3

void update_knn(
    WholeDigitType test_inst,
    WholeDigitType train_inst,
    int min_distances[K_CONST]);