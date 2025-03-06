#include "dfsin.h"

void mul64To128(bits64 a, bits64 b, bits64 *z0Ptr, bits64 *z1Ptr) {
    bits32 aHigh, aLow, bHigh, bLow;
    bits64 z0, zMiddleA, zMiddleB, z1;

    aLow = a;
    aHigh = a >> 32;
    bLow = b;
    bHigh = b >> 32;
    z1 = ((bits64)aLow) * bLow;
    zMiddleA = ((bits64)aLow) * bHigh;
    zMiddleB = ((bits64)aHigh) * bLow;
    z0 = ((bits64)aHigh) * bHigh;
    zMiddleA += zMiddleB;
    z0 += (((bits64)(zMiddleA < zMiddleB)) << 32) + (zMiddleA >> 32);
    zMiddleA <<= 32;
    z1 += zMiddleA;
    z0 += (z1 < zMiddleA);
    *z1Ptr = z1;
    *z0Ptr = z0;
}

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

static bits64 estimateDiv128To64(bits64 a0, bits64 a1, bits64 b) {
    bits64 b0, b1;
    bits64 rem0, rem1, term0, term1;
    bits64 z;

    if (b <= a0)
        return 0xFFFFFFFFFFFFFFFFLL;
    b0 = b >> 32;
    z = (b0 << 32 <= a0) ? 0xFFFFFFFF00000000LL : (a0 / b0) << 32;
    mul64To128(b, z, &term0, &term1);
    sub128(a0, a1, term0, term1, &rem0, &rem1);
    while (((sbits64)rem0) < 0) {
        z -= 0x100000000LL;
        b1 = b << 32;
        add128(rem0, rem1, b0, b1, &rem0, &rem1);
    }
    rem0 = (rem0 << 32) | (rem1 >> 32);
    z |= (b0 << 32 <= rem0) ? 0xFFFFFFFF : rem0 / b0;
    return z;
}

void add128(
    bits64 a0,
    bits64 a1,
    bits64 b0,
    bits64 b1,
    bits64 *z0Ptr,
    bits64 *z1Ptr) {
    bits64 z1;

    z1 = a1 + b1;
    *z1Ptr = z1;
    *z0Ptr = a0 + b0 + (z1 < a1);
}