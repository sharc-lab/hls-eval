#include <iostream>

#include "extractFloat64Sign.h"

int main() {
    // Test inputs and expected outputs
    struct TestCase {
        float64 input;
        flag expectedOutput;
    };

    TestCase testCases[] = {
        {0x0000000000000000ULL, 0}, // +0.0
        {0x8000000000000000ULL, 1}, // -0.0
        {0x3FF0000000000000ULL, 0}, // +1.0
        {0xBFF0000000000000ULL, 1}, // -1.0
        {0x7FF0000000000000ULL, 0}, // +Infinity
        {0xFFF0000000000000ULL, 1}, // -Infinity
        {0x400921FB54442D18ULL, 0}, // +3.14159
        {0xC00921FB54442D18ULL, 1}, // -3.14159
        {0x7FEFFFFFFFFFFFFFULL, 0}, // +Max double
        {0xFFEFFFFFFFFFFFFFULL, 1}, // -Max double
        {0x0010000000000000ULL, 0}, // +Min positive double
        {0x8010000000000000ULL, 1}, // -Min positive double
    };

    // Run test cases
    for (const auto &testCase : testCases) {
        flag result = extractFloat64Sign(testCase.input);
        if (result != testCase.expectedOutput) {
            std::cerr << "Test failed for input 0x" << std::hex
                      << testCase.input << ": expected "
                      << testCase.expectedOutput << ", got " << result
                      << std::endl;
            return 1;
        }
    }

    std::cout << "All tests passed!" << std::endl;
    return 0;
}