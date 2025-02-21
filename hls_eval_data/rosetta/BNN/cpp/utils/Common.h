#ifndef COMMON_H
#define COMMON_H

#include <ap_int.h>
#include <assert.h>
#include <cstdlib>
#include <string>

#include "Typedefs.h"

// Returns the repo's root dir or exits
std::string get_root_dir();

// We encode negative to -1, positive to 0
template <typename T> Bit sgn(const T x) {
#pragma HLS INLINE
    return (x < 0) ? -1 : 0;
}

#endif
