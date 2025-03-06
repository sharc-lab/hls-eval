#include "dfsin.h"

static float64 addFloat64Sigs(float64 a, float64 b, flag zSign) {
    int16 aExp, bExp, zExp;
    bits64 aSig, bSig, zSig;
    int16 expDiff;

    aSig = extractFloat64Frac(a);
    aExp = extractFloat64Exp(a);
    bSig = extractFloat64Frac(b);
    bExp = extractFloat64Exp(b);
    expDiff = aExp - bExp;
    aSig <<= 9;
    bSig <<= 9;
    if (0 < expDiff) {
        if (aExp == 0x7FF) {
            if (aSig)
                return propagateFloat64NaN(a, b);
            return a;
        }
        if (bExp == 0)
            --expDiff;
        else
            bSig |= 0x2000000000000000LL;
        shift64RightJamming(bSig, expDiff, &bSig);
        zExp = aExp;
    } else if (expDiff < 0) {
        if (bExp == 0x7FF) {
            if (bSig)
                return propagateFloat64NaN(a, b);
            return packFloat64(zSign, 0x7FF, 0);
        }
        if (aExp == 0)
            ++expDiff;
        else {
            aSig |= 0x2000000000000000LL;
        }
        shift64RightJamming(aSig, -expDiff, &aSig);
        zExp = bExp;
    } else {
        if (aExp == 0x7FF) {
            if (aSig | bSig)
                return propagateFloat64NaN(a, b);
            return a;
        }
        if (aExp == 0)
            return packFloat64(zSign, 0, (aSig + bSig) >> 9);
        zSig = 0x4000000000000000LL + aSig + bSig;
        zExp = aExp;
        goto roundAndPack;
    }
    aSig |= 0x2000000000000000LL;
    zSig = (aSig + bSig) << 1;
    --zExp;
    if ((sbits64)zSig < 0) {
        zSig = aSig + bSig;
        ++zExp;
    }
roundAndPack:
    return roundAndPackFloat64(zSign, zExp, zSig);
}

void shift64RightJamming(bits64 a, int16 count, bits64 *zPtr) {
    bits64 z;

    if (count == 0) {
        z = a;
    } else if (count < 64) {
        z = (a >> count) | ((a << ((-count) & 63)) != 0);
    } else {
        z = (a != 0);
    }
    *zPtr = z;
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

static void float_raise(int8 flags) { float_exception_flags |= flags; }

bits64 extractFloat64Frac(float64 a) { return a & 0x000FFFFFFFFFFFFFLL; }

int16 extractFloat64Exp(float64 a) { return (a >> 52) & 0x7FF; }

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

float64 packFloat64(flag zSign, int16 zExp, bits64 zSig) {
    return (((bits64)zSign) << 63) + (((bits64)zExp) << 52) + zSig;
}