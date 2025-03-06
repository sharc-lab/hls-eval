#include "extractFloat64Exp.h"
#include <iostream>
#include <cassert>

int main() {
    // Test inputs and expected outputs
    struct TestCase {
        float64 input;
        int16 expectedOutput;
    };

    TestCase testCases[] = {
        {0x3FF0000000000000ULL, 1023},  // 1.0 in IEEE 754
        {0x4000000000000000ULL, 1024},  // 2.0 in IEEE 754
        {0x3FE0000000000000ULL, 1022},  // 0.5 in IEEE 754
        {0x0000000000000000ULL, 0},     // +0.0 in IEEE 754
        {0x8000000000000000ULL, 0},     // -0.0 in IEEE 754
        {0x7FF0000000000000ULL, 2047},  // +Infinity in IEEE 754
        {0xFFF0000000000000ULL, 2047},  // -Infinity in IEEE 754
        {0x7FF8000000000000ULL, 2047},  // NaN in IEEE 754
        {0x40490FDCA0000000ULL, 1028},  // 12.345 in IEEE 754
        {0xC0490FDCA0000000ULL, 1028}   // -12.345 in IEEE 754
    };

    bool allTestsPassed = true;

    for (const auto& testCase : testCases) {
        int16 result = extractFloat64Exp(testCase.input);
        if (result != testCase.expectedOutput) {
            std::cerr << "Test failed for input 0x" << std::hex << testCase.input
                      << ": expected 0x" << std::hex << testCase.expectedOutput
                      << ", got 0x" << std::hex << result << std::dec << std::endl;
            allTestsPassed = false;
        }
    }

    return allTestsPassed ? 0 : 1;
}