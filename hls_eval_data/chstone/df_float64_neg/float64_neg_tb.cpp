
#include <cstdio>

#include "float64_neg.h"

int main() {
    int result = 0;

    struct {
        float64 input;
        float64 expected;
    } test_cases[] = {
        {0x3FF0000000000000ULL, 0xBFF0000000000000ULL}, // 1.0 -> -1.0
        {0xBFF0000000000000ULL, 0x3FF0000000000000ULL}, // -1.0 -> 1.0
        {0x0000000000000000ULL, 0x8000000000000000ULL}, // +0 -> -0
        {0x8000000000000000ULL, 0x0000000000000000ULL}, // -0 -> +0
        {0x7FF0000000000000ULL, 0xFFF0000000000000ULL}, // Inf -> -Inf
        {0xFFF0000000000000ULL, 0x7FF0000000000000ULL}, // -Inf -> Inf
        {0x7FF8000000000000ULL,
         0xFFF8000000000000ULL}, // NaN -> -NaN (sign flip)
        {0x4008000000000000ULL, 0xC008000000000000ULL} // 3.0 -> -3.0
    };

    for (int i = 0; i < 8; ++i) {
        float64 output = float64_neg(test_cases[i].input);
        if (output != test_cases[i].expected) {
            printf(
                "Test case %d FAILED: input = 0x%016llX, expected = 0x%016llX, "
                "got = 0x%016llX\n",
                i,
                test_cases[i].input,
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