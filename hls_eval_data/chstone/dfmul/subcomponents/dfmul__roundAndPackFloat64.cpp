#include "dfmul.h"

int8 float_rounding_mode = 0;
int8 float_exception_flags = 0;

void float_raise(int8 flags) { float_exception_flags |= flags; }

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