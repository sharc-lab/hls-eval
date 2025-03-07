#include <cstdio>

#include "packFloat64.h"

int main() {
    int result = 0;

    struct {
        flag zSign;
        int16 zExp;
        bits64 zSig;
        bits64 expected;
    } test_cases[] = {
        {0, 0x3FF, 0x0000000000000ULL, 0x3FF0000000000000ULL}, // +1.0
        {1, 0x3FF, 0x0000000000000ULL, 0xBFF0000000000000ULL}, // -1.0
        {0, 0x400, 0x0000000000000ULL, 0x4000000000000000ULL}, // +2.0
        {0,
         0x000,
         0x0000000000001ULL,
         0x0000000000000001ULL}, // smallest positive denormal
        {1,
         0x7FF,
         0x0000000000000ULL,
         0xFFF0000000000000ULL}, // negative infinity
        {0, 0x7FF, 0x8000000000000ULL, 0x7FF8000000000000ULL},   // quiet NaN
        {1, 0x400, 0x0008000000000000ULL, 0xC008000000000000ULL} // -3.0
    };

    for (int i = 0; i < 7; ++i) {
        bits64 output = packFloat64(
            test_cases[i].zSign, test_cases[i].zExp, test_cases[i].zSig);
        if (output != test_cases[i].expected) {
            printf(
                "Test case %d FAILED: input = (sign=%d, exp=0x%03X, "
                "sig=0x%013llX), expected = 0x%016llX, got = 0x%016llX\n",
                i,
                test_cases[i].zSign,
                test_cases[i].zExp,
                test_cases[i].zSig,
                test_cases[i].expected,
                output);
            result = 1;
        }
    }

    if (result == 0)
        printf("All tests PASSED.\n");
    else
        printf("Some tests FAILED.\n");

    return result;
}