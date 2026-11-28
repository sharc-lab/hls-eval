#include <cstdint>
#include <cstring>
#include <limits>
#include <cstdio>
#include "float64_ge.h"
#include <iostream>
#include <vector>


// The expected result is independently evaluated with native IEEE binary64.
// Only memcpy transports representation bits; no reference implementation is
// called and no pointer type-punning or integer-to-double conversion is used.
static_assert(sizeof(double) == sizeof(std::uint64_t), "native binary64 required");
static_assert(std::numeric_limits<double>::is_iec559 &&
              std::numeric_limits<double>::digits == 53 &&
              std::numeric_limits<double>::max_exponent == 1024,
              "IEEE binary64 native comparison required");
static_assert(std::numeric_limits<float64>::digits == 64, "64-bit raw carrier required");
#ifdef __FAST_MATH__
#error "The independent IEEE comparison oracle requires fast-math disabled"
#endif

static double native_from_bits(std::uint64_t bits) {
    double result;
    std::memcpy(&result, &bits, sizeof(result));
    return result;
}

static bool check_ieee_matrix() {
    const std::uint64_t patterns[] = {
        // Both zeros.
        0x0000000000000000ULL, 0x8000000000000000ULL,
        // Minimum, multiple small, middle and maximum subnormals, both signs.
        0x0000000000000001ULL, 0x0000000000000002ULL,
        0x0000000000000010ULL, 0x0008000000000000ULL,
        0x000FFFFFFFFFFFFFULL,
        0x8000000000000001ULL, 0x8000000000000002ULL,
        0x8000000000000010ULL, 0x8008000000000000ULL,
        0x800FFFFFFFFFFFFFULL,
        // Minimum normal and its successor, both signs.
        0x0010000000000000ULL, 0x8010000000000000ULL,
        0x0010000000000001ULL, 0x8010000000000001ULL,
        // Several ordinary finite values, both signs.
        0x3FE0000000000000ULL, 0xBFE0000000000000ULL,
        0x3FF0000000000000ULL, 0xBFF0000000000000ULL,
        0x4000000000000000ULL, 0xC000000000000000ULL,
        // Maximum finite and infinity, both signs.
        0x7FEFFFFFFFFFFFFFULL, 0xFFEFFFFFFFFFFFFFULL,
        0x7FF0000000000000ULL, 0xFFF0000000000000ULL,
        // Quiet NaNs with distinct payloads and signs.
        0x7FF8000000000000ULL, 0xFFF8000000000000ULL,
        0x7FF8000000012345ULL, 0xFFF8000000012345ULL,
        // Signalling NaNs, both signs. Only the comparison result is observed;
        // floating exception flags/payload rewriting are not kernel outputs.
        0x7FF0000000000001ULL, 0xFFF0000000000001ULL
    };
    // Refuse a host that collapses subnormal inputs in native comparisons.
    if (!(native_from_bits(0x0000000000000001ULL) > 0.0) ||
        !(native_from_bits(0x8000000000000001ULL) < 0.0)) {
        std::printf("Independent IEEE oracle unavailable: subnormal comparison.\n");
        return false;
    }
    const unsigned count = sizeof(patterns) / sizeof(patterns[0]);
    unsigned failures = 0;
    for (unsigned i = 0; i < count; ++i) {
        for (unsigned j = 0; j < count; ++j) {
            const double a = native_from_bits(patterns[i]);
            const double b = native_from_bits(patterns[j]);
            const flag expected = a >= b ? 1 : 0;
            const flag actual = float64_ge(static_cast<float64>(patterns[i]),
                                          static_cast<float64>(patterns[j]));
            if (actual != expected) {
                if (failures < 16) {
                    std::printf("IEEE matrix failed [%u,%u]: (%016llx,%016llx) actual=%d expected=%d\n",
                                i, j, static_cast<unsigned long long>(patterns[i]),
                                static_cast<unsigned long long>(patterns[j]), actual, expected);
                }
                ++failures;
            }
        }
    }
    std::printf("IEEE matrix checked %u ordered pairs; failures=%u.\n", count * count, failures);
    return failures == 0;
}

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

    if (!check_ieee_matrix()) fail = 1;

    if (fail == 0) {
        printf("All test cases passed successfully.\n");
    }

    return fail;
}