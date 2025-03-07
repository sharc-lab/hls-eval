#include "float64_is_nan.h"
#include <iostream>

int main() {
    // Test inputs
    float64 testInputs[] = {
        0x7FF8000000000000LL, // NaN
        0xFFF8000000000000LL, // NaN
        0x7FF0000000000000LL, // Infinity
        0xFFF0000000000000LL, // -Infinity
        0x0000000000000000LL, // 0.0
        0x8000000000000000LL, // -0.0
        0x7FEFFFFFFFFFFFFFLL, // Largest finite positive number
        0xFFEFFFFFFFFFFFFFLL, // Largest finite negative number
        0x7FF7FFFFFFFFFFFFLL, // SNaN
        0xFFF7FFFFFFFFFFFFLL  // -SNaN
    };

    // Expected outputs
    flag expectedOutputs[] = {
        1, // NaN
        1, // NaN
        0, // Infinity
        0, // -Infinity
        0, // 0.0
        0, // -0.0
        0, // Largest finite positive number
        0, // Largest finite negative number
        1, // SNaN
        1  // -SNaN
    };

    // Number of test cases
    int numTests = sizeof(testInputs) / sizeof(testInputs[0]);

    // Run the test cases
    for (int i = 0; i < numTests; ++i) {
        flag result = float64_is_nan(testInputs[i]);
        if (result != expectedOutputs[i]) {
            std::cerr << "Test failed for input " << std::hex << testInputs[i]
                      << std::dec << ": expected " << expectedOutputs[i]
                      << ", got " << result << std::endl;
            return 1;
        }
    }

    std::cout << "All tests passed!" << std::endl;
    return 0;
}