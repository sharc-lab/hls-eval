#include <cstdio>

#include "mul64To128.h"

int main() {
    int result = 0;

    struct {
        bits64 a;
        bits64 b;
        bits64 expected_high;
        bits64 expected_low;
    } test_cases[] = {
        {0x0000000100000000ULL,
         0x0000000100000000ULL,
         0x0000000000000001ULL,
         0x0000000000000000ULL},
        {0xFFFFFFFFFFFFFFFFULL,
         0xFFFFFFFFFFFFFFFFULL,
         0xFFFFFFFFFFFFFFFEULL,
         0x0000000000000001ULL},
        {0x123456789ABCDEF0ULL,
         0x0FEDCBA987654321ULL,
         0x0121FA00AD77D742ULL,
         0x2236D88FE5618CF0ULL},
        {0x0000000000000000ULL,
         0xFFFFFFFFFFFFFFFFULL,
         0x0000000000000000ULL,
         0x0000000000000000ULL},
        {0xFFFFFFFFFFFFFFFFULL,
         0x0000000000000001ULL,
         0x0000000000000000ULL,
         0xFFFFFFFFFFFFFFFFULL},
    };

    for (int i = 0; i < 5; ++i) {
        bits64 high, low;
        mul64To128(test_cases[i].a, test_cases[i].b, &high, &low);
        if (high != test_cases[i].expected_high ||
            low != test_cases[i].expected_low) {
            printf(
                "Test case %d FAILED: a = 0x%016llX, b = 0x%016llX, expected = "
                "(0x%016llX, 0x%016llX), got = (0x%016llX, 0x%016llX)\n",
                i,
                test_cases[i].a,
                test_cases[i].b,
                test_cases[i].expected_high,
                test_cases[i].expected_low,
                high,
                low);
            result = 1;
        }
    }

    if (result == 0)
        printf("All tests PASSED.\n");
    else
        printf("Some tests FAILED.\n");

    return result;
}