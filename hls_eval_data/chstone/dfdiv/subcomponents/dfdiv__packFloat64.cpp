#include "dfdiv.h"

int8 float_rounding_mode = 0;
int8 float_exception_flags = 0;

float64 packFloat64(flag zSign, int16 zExp, bits64 zSig) {
    return (((bits64)zSign) << 63) + (((bits64)zExp) << 52) + zSig;
}