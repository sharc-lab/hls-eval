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

void shift64ExtraRightJamming(
    bits64 a0,
    bits64 a1,
    int16 count,
    bits64 *z0Ptr,
    bits64 *z1Ptr) {
    bits64 z0, z1;
    int8 negCount;
    negCount = (-count) & 63;

    if (count == 0) {
        z1 = a1;
        z0 = a0;
    } else if (count < 64) {
        z1 = (a0 << negCount) | (a1 != 0);
        z0 = a0 >> count;
    } else {
        if (count == 64) {
            z1 = a0 | (a1 != 0);
        } else {
            z1 = ((a0 | a1) != 0);
        }
        z0 = 0;
    }
    *z1Ptr = z1;
    *z0Ptr = z0;
}