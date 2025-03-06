int8 float_rounding_mode = 0;
int8 float_exception_flags = 0;

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

void float_raise(int8 flags) { float_exception_flags |= flags; }

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
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    int8 shiftCount;

    shiftCount = 0;
    if (a < 0x10000) {
        shiftCount += 16;
        a <<= 16;
    }
    if (a < 0x1000000) {
        shiftCount += 8;
        a <<= 8;
    }
    shiftCount += countLeadingZerosHigh[a >> 24];
    return shiftCount;
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
            float_raise(8