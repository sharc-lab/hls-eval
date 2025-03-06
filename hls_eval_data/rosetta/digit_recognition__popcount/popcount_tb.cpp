#include "popcount.h"
#include <cstdio>

int main() {
    int fail_flag = 0;

    struct TestCase {
        WholeDigitType input;
        int expected;
    };

    TestCase testcases[] = {
        {WholeDigitType(0x0), 0}, // No bits set
        {WholeDigitType(0x1), 1}, // Single bit set
        {WholeDigitType(0xFFFFFFFFFFFFFFFF),
         64},                      // All bits set in lower 64 bits
        {WholeDigitType(-1), 256}, // All 256 bits set
        {WholeDigitType(0xF0F0F0F0F0F0F0F0), 32}, // Alternating pattern
        {WholeDigitType(0xAAAAAAAAAAAAAAAA), 32}, // Another alternating pattern
        {WholeDigitType(0x000000000000FFFF), 16}, // Lower 16 bits set
    };

    for (const auto &tc : testcases) {
        int result = popcount(tc.input);
        if (result != tc.expected) {
            printf(
                "Test failed: input = %llu, expected = %d, got = %d\n",
                (unsigned long long)tc.input,
                tc.expected,
                result);
            fail_flag = 1;
        }
    }

    return fail_flag;
}
