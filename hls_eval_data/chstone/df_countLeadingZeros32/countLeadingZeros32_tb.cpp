#include "countLeadingZeros32.h"
#include <iostream>

int main() {
    int test_result = 0;

    // Test cases
    bits32 test_inputs[] = {
        0x80000000,
        0x7FFFFFFF,
        0xFFFFFFFF,
        0x00000001,
        0x00000000,
        0x10000000,
        0x08000000,
        0x00008000,
        0x00000080,
        0x00000002,
    };
    int8 expected_outputs[] = {
        0,
        1,
        0,
        31,
        32,
        3,
        4,
        16,
        24,
        30,
    };
    int num_tests = sizeof(test_inputs) / sizeof(test_inputs[0]);

    // Run tests
    for (int i = 0; i < num_tests; ++i) {
        int8 actual_output = countLeadingZeros32(test_inputs[i]);
        if (actual_output != expected_outputs[i]) {
            std::cout << "Test case " << i << " failed:" << std::endl;
            std::cout << "  Input: 0x" << std::hex << test_inputs[i]
                      << std::endl;
            std::cout << "  Expected output: " << std::dec
                      << (int)expected_outputs[i] << std::endl;
            std::cout << "  Actual output: " << std::dec << (int)actual_output
                      << std::endl;
            test_result = 1; // Set error flag
        } else {
            std::cout << "Test case " << i << " passed." << std::endl;
        }
    }

    if (test_result == 0) {
        std::cout << "All tests passed!" << std::endl;
    } else {
        std::cout << "Some tests failed." << std::endl;
    }

    return test_result;
}