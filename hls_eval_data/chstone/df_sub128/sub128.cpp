#include "sub128.h"

void sub128(
    bits64 a0,
    bits64 a1,
    bits64 b0,
    bits64 b1,
    bits64 *z0Ptr,
    bits64 *z1Ptr) {

    *z1Ptr = a1 - b1;
    *z0Ptr = a0 - b0 - (a1 < b1);
}