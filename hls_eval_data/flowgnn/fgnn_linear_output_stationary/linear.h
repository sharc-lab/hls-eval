#include <array>
using std::array;

#include "hls_stream.h"

typedef float FM_TYPE;
typedef float WT_TYPE;

#define DIM_IN 32
#define DIM_OUT 16
#define PARALLEL 4
#define RELU 1

void linear_output_stationary(
    FM_TYPE input[DIM_IN],
    WT_TYPE weight[DIM_OUT][DIM_IN],
    WT_TYPE bias[DIM_OUT],
    hls::stream<array<FM_TYPE, PARALLEL>> &output);