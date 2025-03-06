#include <iostream>

#include "extractFloat64Frac.h"

int main() {
    int errors = 0;

    // Define test cases: pairs of input and expected output
    struct {
        float64 input;
        bits64 expected_output;
    } test_cases[] = {
        {0x3FF0000000000000ULL, 0x0000000000000000ULL}, // 1.0
        {0xBFF0000000000000ULL, 0x0000000000000000ULL}, // -1.0
        {0x4008000000000000ULL, 0x0008000000000000ULL}, // 3.0
        {0x7FF0000000000000ULL, 0x0000000000000000ULL}, // Inf
        {0xFFF8000000000000ULL, 0x0008000000000000ULL}, // NaN
        {0x000FFFFFFFFFFFFFULL, 0x000FFFFFFFFFFFFFULL}, // Smallest subnormal
        {0x0000000000000000ULL, 0x0000000000000000ULL}, // Zero
        {0x8000000000000000ULL, 0x0000000000000000ULL}, // Negative Zero
        {0x7FF8000000000000ULL, 0x0008000000000000ULL}, // Quiet NaN
        {0x3FEFFFFFFFFFFFFFULL, 0x000FFFFFFFFFFFFFULL}  // Largest fraction
    };

    int num_cases = sizeof(test_cases) / sizeof(test_cases[0]);

    for (int i = 0; i < num_cases; i++) {
        bits64 result = extractFloat64Frac(test_cases[i].input);

        if (result != test_cases[i].expected_output) {
            printf(
                "Test case %d failed: input=0x%016llX, expected=0x%016llX, "
                "got=0x%016llX\n",
                i,
                test_cases[i].input,
                test_cases[i].expected_output,
                result);
            errors++;
        }
    }

    if (errors) {
        printf("%d test case(s) failed.\n", errors);
        return 1;
    } else {
        printf("All test cases passed!\n");
        return 0;
    }
}