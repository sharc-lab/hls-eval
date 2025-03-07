#include <stdio.h>

#include "propagateFloat64NaN.h"

typedef unsigned long long bits64;
typedef unsigned long long float64;
typedef int flag;

int main() {
    int result = 0;

    struct {
        float64 a;
        float64 b;
        float64 expected;
    } test_cases[] = {
        {0x7FF8000000000000ULL,
         0x3FF0000000000000ULL,
         0x7FF8000000000000ULL}, // Quiet NaN, normal
        {0x7FF0000000000001ULL,
         0x3FF0000000000000ULL,
         0x7FF8000000000001ULL}, // Signaling NaN a
        {0x3FF0000000000000ULL,
         0x7FF0000000000001ULL,
         0x7FF8000000000001ULL}, // Signaling NaN b
        {0x7FF8000000000001ULL,
         0x7FF8000000000002ULL,
         0x7FF8000000000002ULL}, // Both quiet NaNs
        {0x7FF0000000000001ULL,
         0x7FF8000000000000ULL,
         0x7FF8000000000001ULL}, // Signaling a, quiet b
        {0x7FF8000000000000ULL,
         0x7FF0000000000001ULL,
         0x7FF8000000000001ULL}, // Quiet a, signaling b
        {0x7FF8000000000000ULL,
         0x7FF0000000000000ULL,
         0x7FF8000000000000ULL} // Quiet NaN vs Infinity

    };

    for (int i = 0; i < 7; ++i) {
        float64 output = propagateFloat64NaN(test_cases[i].a, test_cases[i].b);
        if (output != test_cases[i].expected) {
            printf(
                "Test case %d FAILED: input = (0x%016llX, 0x%016llX), expected "
                "= 0x%016llX, got = 0x%016llX\n",
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
