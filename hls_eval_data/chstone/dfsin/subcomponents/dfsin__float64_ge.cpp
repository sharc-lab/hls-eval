flag float64_ge(float64 a, float64 b) { return float64_le(b, a); }

flag float64_le(float64 a, float64 b) {
    flag aSign, bSign;

    if (((extractFloat64Exp(a) == 0x7FF) && extractFloat64Frac(a)) ||
        ((extractFloat64Exp(b) == 0x7FF) && extractFloat64Frac(b))) {
        float_raise(16);
        return 0;
    }
    aSign = extractFloat64Sign(a);
    bSign = extractFloat64Sign(b);
    if (aSign != bSign)
        return aSign || ((bits64)((a | b) << 1) == 0);
    return (a == b) || (aSign ^ (a < b));
}

flag extractFloat64Sign(float64 a) { return a >> 63; }

int16 extractFloat64Exp(float64 a) { return (a >> 52) & 0x7FF; }

void float_raise(int8 flags) { float_exception_flags |= flags; }