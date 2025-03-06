int8 float_rounding_mode = 0;
int8 float_exception_flags = 0;

void float_raise(int8 flags) { float_exception_flags |= flags; }

bits64 extractFloat64Frac(float64 a) { return a & 0x000FFFFFFFFFFFFFLL; }

int16 extractFloat64Exp(float64 a) { return (a >> 52) & 0x7FF; }

flag extractFloat64Sign(float64 a) { return a >> 63; }

static void
normalizeFloat64Subnormal(bits64 aSig, int16 *zExpPtr, bits64 *zSigPtr) {
    int8 shiftCount;

    shiftCount = countLeadingZeros64(aSig) - 11;
    *zSigPtr = aSig << shiftCount;
    *zExpPtr = 1 - shiftCount;
}

float64 packFloat64(flag zSign, int16 zExp, bits64 zSig) {

    return (((bits64)zSign) << 63) + (((bits64)zExp) << 52) + zSig;
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
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
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

static float64
normalizeRoundAndPackFloat64(flag zSign, int16 zExp, bits64 zSig) {
    int8 shiftCount;

    shiftCount = countLeadingZeros64(zSig) - 1;
    return roundAndPackFloat64(zSign, zExp - shiftCount, zSig << shiftCount);
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