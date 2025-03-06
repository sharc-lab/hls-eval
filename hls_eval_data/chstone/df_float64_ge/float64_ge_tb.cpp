#include "float64_ge.h"
#include <iostream>
#include <vector>

int main() {
    int fail = 0;

    // Define test cases
    struct {
        float64 a;
        float64 b;
        flag expected;
    } test_cases[] = {
        {0x4000000000000000ULL, 0x3FF0000000000000ULL, 1}, // 2.0 >= 1.0
        {0x3FF0000000000000ULL, 0x4000000000000000ULL, 0}, // 1.0 >= 2.0
        {0xBFF0000000000000ULL, 0x3FF0000000000000ULL, 0}, // -1.0 >= 1.0
        {0x7FF8000000000000ULL, 0x3FF0000000000000ULL, 0}, // NaN >= 1.0
        {0x3FF0000000000000ULL, 0x3FF0000000000000ULL, 1}, // 1.0 >= 1.0
        {0x0000000000000000ULL, 0x8000000000000000ULL, 1}, // 0.0 >= -0.0
        {0x8000000000000000ULL, 0x0000000000000000ULL, 1}, // -0.0 >= 0.0
        {0xFFF0000000000000ULL, 0xFFF0000000000000ULL, 1}, // -inf >= -inf
        {0x7FF0000000000000ULL, 0x3FF0000000000000ULL, 1}, // +inf >= 1.0
        {0x3FF0000000000000ULL, 0x7FF0000000000000ULL, 0}, // 1.0 >= +inf
    };

    const int NUM_TESTS = sizeof(test_cases) / sizeof(test_cases[0]);

    for (int i = 0; i < NUM_TESTS; i++) {
        flag result = float64_ge(test_cases[i].a, test_cases[i].b);
        if (result != test_cases[i].expected) {
            printf(
                "Test case %d failed: float64_ge(%llx, %llx) = %d, expected "
                "%d\n",
                i,
                test_cases[i].a,
                test_cases[i].b,
                result,
                test_cases[i].expected);
            fail = 1;
        }
    }

    if (fail == 0) {
        printf("All test cases passed successfully.\n");
    }

    return fail;
}