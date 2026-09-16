#ifndef STREAMCLUSTER_H
#define STREAMCLUSTER_H

#include <string.h>
#include "ap_fixed.h"
// work_mem accumulates cost differences across BATCH_SIZE=1024 points with
// DIM=200 features, reaching magnitudes of ~2e5 -- ap_fixed<32,16>'s 16
// integer bits (max ~32767) silently overflow/wrap there, so widen the
// integer part while keeping 16 fractional bits for precision.
typedef ap_fixed<48, 32> fixed_t;

#define OFFSET 1  
//2973//((OFFSET) << 17)
//#define BATCH_SIZE 1024
#define DIM 200
#define BATCH_SIZE 1024
#define MAX_WORK_MEM_SIZE 128

struct bench_args_t {
    
};
#endif