#include <stdio.h>

#include "add128.h"

typedef struct {
    bits64 a0;
    bits64 a1;
    bits64 b0;
    bits64 b1;
    bits64 expected_z0;
    bits64 expected_z1;
} TestCase;

int main() {
    bits64 z0, z1;

    TestCase tests[] = {{0ULL, 0ULL, 0ULL, 0ULL, 0ULL, 0ULL},
                        {0xFFFFFFFFFFFFFFFFULL, 0ULL, 1ULL, 0ULL, 0ULL, 0ULL},
                        {0ULL, 0xFFFFFFFFFFFFFFFFULL, 0ULL, 1ULL, 1ULL, 0ULL},
                        {0x123456789ABCDEF0ULL,
                         0x0FEDCBA987654321ULL,
                         0x1111111111111111ULL,
                         0x2222222222222222ULL,
                         0x23456789ABCDF001ULL,
                         0x320FEDCBA9876543ULL},
                        {0xFFFFFFFFFFFFFFFFULL,
                         0xFFFFFFFFFFFFFFFFULL,
                         0xFFFFFFFFFFFFFFFFULL,
                         0xFFFFFFFFFFFFFFFFULL,
                         0xFFFFFFFFFFFFFFFFULL,
                         0xFFFFFFFFFFFFFFFEULL}};

    int num_tests = sizeof(tests) / sizeof(TestCase);
    int fail = 0;

    for (int i = 0; i < num_tests; ++i) {
        add128(tests[i].a0, tests[i].a1, tests[i].b0, tests[i].b1, &z0, &z1);
        if (z0 != tests[i].expected_z0 || z1 != tests[i].expected_z1) {
            printf(
                "Test %d failed: Got z0=0x%llx, z1=0x%llx; Expected z0=0x%llx, "
                "z1=0x%llx\n",
                i,
                z0,
                z1,
                tests[i].expected_z0,
                tests[i].expected_z1);
            fail = 1;
        } else {
            printf("Test %d passed.\n", i);
        }
    }

    if (fail) {
        printf("Some tests FAILED.\n");
        return 1;
    } else {
        printf("All tests PASSED.\n");
        return 0;
    }
}