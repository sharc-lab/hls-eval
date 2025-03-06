#include <cstdio>

#include "float64_is_signaling_nan.h"

int main() {
    int result = 0;

    // Test cases (hex representation of IEEE 754 double precision)
    float64 test_cases[] = {
        0x7FF8000000000001ULL, // Quiet NaN (should be 0)
        0x7FF0000000000001ULL, // Signaling NaN (should be 1)
        0x7FF7FFFFFFFFFFFFULL, // Signaling NaN (should be 1)
        0x7FF8000000000000ULL, // Quiet NaN (should be 0)
        0x0000000000000000ULL, // Zero (should be 0)
        0x3FF0000000000000ULL, // 1.0 (should be 0)
        0xFFF0000000000001ULL, // Negative signaling NaN (should be 1)
        0xFFF8000000000000ULL  // Negative quiet NaN (should be 0)
    };

    flag expected_results[] = {0, 1, 1, 0, 0, 0, 1, 0};

    int num_tests = sizeof(test_cases) / sizeof(test_cases[0]);

    for (int i = 0; i < num_tests; i++) {
        flag output = float64_is_signaling_nan(test_cases[i]);
        if (output != expected_results[i]) {
            printf(
                "Test case %d FAILED: input = 0x%016llX, expected = %d, got = "
                "%d\n",
                i,
                test_cases[i],
                expected_results[i],
                output);
            result = 1;
        } else {
            printf("Test case %d PASSED\n", i);
        }
    }

    if (result == 0) {
        printf("All tests PASSED.\n");
    } else {
        printf("Some tests FAILED.\n");
    }

    return result;
}