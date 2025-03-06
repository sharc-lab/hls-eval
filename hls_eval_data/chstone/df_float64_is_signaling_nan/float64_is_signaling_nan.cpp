#include "float64_is_signaling_nan.h"

flag float64_is_signaling_nan(float64 a) {
    return (((a >> 51) & 0xFFF) == 0xFFE) && (a & 0x0007FFFFFFFFFFFFLL);
}