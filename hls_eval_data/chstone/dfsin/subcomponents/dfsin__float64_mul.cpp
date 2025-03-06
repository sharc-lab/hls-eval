#include "dfsin.h"

float64 float64_mul(float64 a, float64 b) {
    flag aSign, bSign, zSign;
    int16 aExp, bExp, zExp;
    bits64 aSig, bSig, zSig0, zSig1;

    aSig = extractFloat64Frac(a);
    aExp = extractFloat64Exp(a);
    aSign = extractFloat64Sign(a);
    bSig = extractFloat64Frac(b);
    bExp = extractFloat64Exp(b);
    bSign = extractFloat64Sign(b);
    zSign = aSign ^ bSign;
    if (aExp == 0x7FF) {
        if (aSig || ((bExp == 0x7FF) && bSig))
            return propagateFloat64NaN(a, b);
        if ((bExp | bSig) == 0) {
            float_raise(16);
            return 0x7FFFFFFFFFFFFFFFLL;
        }
        return packFloat64(zSign, 0x7FF, 0);
    }
    if (bExp == 0x7FF) {
        if (bSig)
            return propagateFloat64NaN(a, b);
        if ((aExp | aSig) == 0) {
            float_raise(16);
            return 0x7FFFFFFFFFFFFFFFLL;
        }
        return packFloat64(zSign, 0x7FF, 0);
    }
    if (aExp == 0) {
        if (aSig == 0)
            return packFloat64(zSign, 0, 0);
        normalizeFloat64Subnormal(aSig, &aExp, &aSig);
    }
    if (bExp == 0) {
        if (bSig == 0)
            return packFloat64(zSign, 0, 0);
        normalizeFloat64Subnormal(bSig, &bExp, &bSig);
    }
    zExp = aExp + bExp - 0x3FF;
    aSig = (aSig | 0x0010000000000000LL) << 10;
    bSig = (bSig | 0x0010000000000000LL) << 11;
    mul64To128(aSig, bSig, &zSig0, &zSig1);
    zSig0 |= (zSig1 != 0);
    if (0 <= (sbits64)(zSig0 << 1)) {
        zSig0 <<= 1;
        --zExp;
    }
    return roundAndPackFloat64(zSign, zExp, zSig0);
}

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

static float64 propagateFloat64NaN(float64 a, float64 b) {
    flag aIsNaN, aIsSignalingNaN, bIsNaN, bIsSignalingNaN;

    aIsNaN = float64_is_nan(a);
    aIsSignalingNaN = float64_is_signaling_nan(a);
    bIsNaN = float64_is_nan(b);
    bIsSignalingNaN = float64_is_signaling_nan(b);
    a |= 0x0008000000000000LL;
    b |= 0x0008000000000000LL;
    if (aIsSignalingNaN | bIsSignalingNaN)
        float_raise(16);
    return bIsSignalingNaN ? b : aIsSignalingNaN ? a : bIsNaN ? b : a;
}

flag float64_is_nan(float64 a) {
    return (0xFFE0000000000000LL < (bits64)(a << 1));
}

flag float64_is_signaling_nan(float64 a) {
    return (((a >> 51) & 0xFFF) == 0xFFE) && (a & 0x0007FFFFFFFFFFFFLL);
}

static void normalizeFloat64Subnormal(bits64 aSig, int16 *zExpPtr, bits64 *zSigPtr) {
    int8 shiftCount;

    shiftCount = countLeadingZeros64(aSig) - 11;
    *zSigPtr = aSig << shiftCount;
    *zExpPtr = 1 - shiftCount;
}

float64 packFloat64(flag zSign, int16 zExp, bits64 zSig) {
    return (((bits64)zSign) << 63) + (((bits64)zExp) << 52) + zSig;
}

static float64 roundAndPackFloat64(flag zSign, int16 zExp, bits64 zSig) {
    int8 roundingMode;
    flag roundNearestEven, isTiny;
    int16 roundIncrement, roundBits;

    roundingMode = float_rounding_mode;
    roundNearestEven = (roundingMode == 0);
    roundIncrement = 0x200;
    if (!roundNearestEven) {
        if (roundingMode == 1) {
            roundIncrement = 0;
        } else {
            roundIncrement = 0x3FF;
            if (zSign) {
                if (roundingMode == 2)
                    roundIncrement = 0;
            } else {
                if (roundingMode == 3)
                    roundIncrement = 0;
            }
        }
    }
    roundBits = zSig & 0x3FF;
    if (0x7FD <= (bits16)zExp) {
        if ((0x7FD < zExp) ||
            ((zExp == 0x7FD) && ((sbits64)(zSig + roundIncrement) < 0))) {
            float_raise(8 | 1);
            return packFloat64(zSign, 0x7FF, 0) - (roundIncrement == 0);
        }
        if (zExp < 0) {
            isTiny = (1 == 1) || (zExp < -1) ||
                     (zSig + roundIncrement < 0x8000000000000000LL);
            shift64RightJamming(zSig, -zExp, &zSig);
            zExp = 0;
            roundBits = zSig & 0x3FF;
            if (isTiny && roundBits)
                float_raise(4);
        }
    }
    if (roundBits)
        float_exception_flags |= 1;
    zSig = (zSig + roundIncrement) >> 10;
    zSig &= ~(((roundBits ^ 0x200) == 0) & roundNearestEven);
    if (zSig == 0)
        zExp = 0;
    return packFloat64(zSign, zExp, zSig);
}

static int8 countLeadingZeros64(bits64 a) {
    int8 shiftCount;

    shiftCount = 0;
    if (a < ((bits64)1) << 32) {
        shiftCount += 32;
    } else {
        a >>= 32;
    }
    shiftCount += countLeadingZeros32(a);
    return shiftCount;
}

static int8 countLeadingZeros32(bits32 a) {
    static const int8 countLeadingZerosHigh[256] = {
        8, 7, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3,
        3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2