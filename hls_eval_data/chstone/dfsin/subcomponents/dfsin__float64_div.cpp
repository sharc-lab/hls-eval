float64 float64_div(float64 a, float64 b) {
    flag aSign, bSign, zSign;
    int16 aExp, bExp, zExp;
    bits64 aSig, bSig, zSig;
    bits64 rem0, rem1, term0, term1;

    aSig = extractFloat64Frac(a);
    aExp = extractFloat64Exp(a);
    aSign = extractFloat64Sign(a);
    bSig = extractFloat64Frac(b);
    bExp = extractFloat64Exp(b);
    bSign = extractFloat64Sign(b);
    zSign = aSign ^ bSign;
    if (aExp == 0x7FF) {
        if (aSig)
            return propagateFloat64NaN(a, b);
        if (bExp == 0x7FF) {
            if (bSig)
                return propagateFloat64NaN(a, b);
            float_raise(16);
            return 0x7FFFFFFFFFFFFFFFLL;
        }
        return packFloat64(zSign, 0x7FF, 0);
    }
    if (bExp == 0x7FF) {
        if (bSig)
            return propagateFloat64NaN(a, b);
        return packFloat64(zSign, 0, 0);
    }
    if (bExp == 0) {
        if (bSig == 0) {
            if ((aExp | aSig) == 0) {
                float_raise(16);
                return 0x7FFFFFFFFFFFFFFFLL;
            }
            float_raise(2);
            return packFloat64(zSign, 0x7FF, 0);
        }
        normalizeFloat64Subnormal(bSig, &bExp, &bSig);
    }
    if (aExp == 0) {
        if (aSig == 0)
            return packFloat64(zSign, 0, 0);
        normalizeFloat64Subnormal(aSig, &aExp, &aSig);
    }
    zExp = aExp - bExp + 0x3FD;
    aSig = (aSig | 0x0010000000000000LL) << 10;
    bSig = (bSig | 0x0010000000000000LL) << 11;
    if (bSig <= (aSig + aSig)) {
        aSig >>= 1;
        ++zExp;
    }
    zSig = estimateDiv128To64(aSig, 0, bSig);
    if ((zSig & 0x1FF) <= 2) {
        mul64To128(bSig, zSig, &term0, &term1);
        sub128(aSig, 0, term0, term1, &rem0, &rem1);
        while ((sbits64)rem0 < 0) {
            --zSig;
            add128(rem0, rem1, 0, bSig, &rem0, &rem1);
        }
        zSig |= (rem1 != 0);
    }
    return roundAndPackFloat64(zSign, zExp, zSig);
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

static void
normalizeFloat64Subnormal(bits64 aSig, int16 *zExpPtr, bits64 *zSigPtr) {
    int8 shiftCount;

    shiftCount = countLeadingZeros64(aSig) - 11;
    *zSigPtr = aSig << shiftCount;
    *zExpPtr = 1 - shiftCount;
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
    static const int8 countLeadingZerosHigh[256