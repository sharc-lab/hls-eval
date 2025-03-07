#include "propagateFloat64NaN.h"

flag float64_is_nan(float64 a) {
    return (0xFFE0000000000000LL < (bits64)(a << 1));
}

flag float64_is_signaling_nan(float64 a) {
    return (((a >> 51) & 0xFFF) == 0xFFE) && (a & 0x0007FFFFFFFFFFFFLL);
}

float64 propagateFloat64NaN(float64 a, float64 b) {
    flag aIsNaN, aIsSignalingNaN, bIsNaN, bIsSignalingNaN;

    aIsNaN = float64_is_nan(a);
    aIsSignalingNaN = float64_is_signaling_nan(a);
    bIsNaN = float64_is_nan(b);
    bIsSignalingNaN = float64_is_signaling_nan(b);
    a |= 0x0008000000000000LL;
    b |= 0x0008000000000000LL;
    return bIsSignalingNaN ? b : aIsSignalingNaN ? a : bIsNaN ? b : a;
}