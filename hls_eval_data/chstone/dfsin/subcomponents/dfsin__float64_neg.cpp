float64 float64_neg(float64 x) {
    return (((~x) & 0x8000000000000000ULL) | (x & 0x7fffffffffffffffULL));
}