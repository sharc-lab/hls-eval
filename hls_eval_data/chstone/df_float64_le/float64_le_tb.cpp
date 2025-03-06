#include <cstdio>

#include "float64_le.h"

int main() {
    int result = 0;

    // Test cases: pairs of numbers and expected results (1 if a <= b, else 0)
    struct {
        float64 a;
        float64 b;
        flag expected;
    } test_cases[] = {
        {0x3FF0000000000000ULL, 0x4000000000000000ULL, 1}, // 1.0 <= 2.0
        {0x4000000000000000ULL, 0x3FF0000000000000ULL, 0}, // 2.0 <= 1.0
        {0x7FF0000000000000ULL, 0x3FF0000000000000ULL, 0}, // Inf <= 1.0
        {0xBFF0000000000000ULL, 0x3FF0000000000000ULL, 1}, // -1.0 <= 1.0
        {0x0000000000000000ULL, 0x8000000000000000ULL, 1}, // +0 <= -0
        {0x8000000000000000ULL, 0x0000000000000000ULL, 1}, // -0 <= +0
        {0x7FF8000000000000ULL,
         0x3FF0000000000000ULL,
         0}, // NaN <= 1.0 (should be 0)
        {0x3FF0000000000000ULL, 0x7FF8000000000000ULL, 0}, // 1.0 <= NaN
        {0xBFF0000000000000ULL, 0x4000000000000000ULL, 1}, // -1.0 <= 2.0
        {0x4000000000000000ULL, 0x4000000000000000ULL, 1}  // 2.0 <= 2.0
    };

    for (int i = 0; i < 10; ++i) {
        flag output = float64_le(test_cases[i].a, test_cases[i].b);
        if (output != test_cases[i].expected) {
            printf(
                "Test case %d FAILED: input = (0x%016llX, 0x%016llX), expected "
                "= %d, got = %d\n",
                i,
                test_cases[i].a,
                test_cases[i].b,
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