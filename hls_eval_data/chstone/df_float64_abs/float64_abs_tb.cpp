#include "float64_abs.h"

#include <iostream>

int main() {
    int fail = 0;

    // Test cases: pairs of input and expected output
    struct {
        float64 input;
        float64 expected;
    } tests[] = {
        {0x8000000000000000ULL, 0x0000000000000000ULL}, // negative zero
        {0x0000000000000000ULL, 0x0000000000000000ULL}, // positive zero
        {0xBFF0000000000000ULL, 0x3FF0000000000000ULL}, // -1.0 -> 1.0
        {0x3FF0000000000000ULL, 0x3FF0000000000000ULL}, // 1.0 -> 1.0
        {0xFFF0000000000000ULL,
         0x7FF0000000000000ULL}, // negative infinity -> infinity
        {0x7FF0000000000000ULL, 0x7FF0000000000000ULL}, // positive infinity
        {0xFFFFFFFFFFFFFFFFULL,
         0x7FFFFFFFFFFFFFFFULL}, // NaN or extreme negative
        {0xC008000000000000ULL, 0x4008000000000000ULL}, // -3.0 -> 3.0
        {0x4008000000000000ULL, 0x4008000000000000ULL}, // 3.0 -> 3.0
        {0xC024000000000000ULL, 0x4024000000000000ULL}, // -10.0 -> 10.0
        {0x4024000000000000ULL, 0x4024000000000000ULL}, // 10.0 -> 10.0
        {0xC059000000000000ULL, 0x4059000000000000ULL}, // -100.0 -> 100.0
        {0x4059000000000000ULL, 0x4059000000000000ULL}, // 100.0 -> 100.0
    };

    const int num_tests = sizeof(tests) / sizeof(tests[0]);

    for (int i = 0; i < num_tests; i++) {
        if (float64_abs(tests[i].input) != tests[i].expected) {
            printf(
                "Test %d FAILED: input=0x%016llx, expected=0x%016llx, "
                "got=0x%016llx\n",
                i,
                tests[i].input,
                tests[i].expected,
                float64_abs(tests[i].input));
            fail = 1;
        } else {
            printf(
                "Test %d PASSED: input=0x%016llx, output=0x%016llx\n",
                i,
                tests[i].input,
                tests[i].expected);
        }
    }

    return fail;
}
