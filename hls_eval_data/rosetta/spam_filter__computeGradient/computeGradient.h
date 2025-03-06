#include "ap_fixed.h"

#define FTYPE_TWIDTH 32
#define FTYPE_IWIDTH 13
typedef ap_fixed<FTYPE_TWIDTH, FTYPE_IWIDTH> FeatureType;

#define DTYPE_TWIDTH 16
#define DTYPE_IWIDTH 4
typedef ap_fixed<DTYPE_TWIDTH, DTYPE_IWIDTH> DataType;

const int NUM_FEATURES = 1024;
#define PAR_FACTOR 32

void computeGradient(
    FeatureType grad[NUM_FEATURES],
    DataType feature[NUM_FEATURES],
    FeatureType scale);