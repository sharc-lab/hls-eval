#include <iostream>
#include <limits>
#include <ostream>

#include "countLeadingZeros64.h"

int main() {
    int fail_flag = 0;
    bits64 test_value;
    int8 expected_result;
    int8 actual_result;

    // Test case 1: Zero
    test_value = 0;
    expected_result = 64;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 1 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    // Test case 2: All ones
    test_value = std::numeric_limits<bits64>::max();
    expected_result = 0;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 2 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    // Test case 3: Single one at the MSB
    test_value = ((bits64)1) << 63;
    expected_result = 0;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 3 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    // Test case 4: Single one at the LSB
    test_value = 1;
    expected_result = 63;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 4 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    // Test case 5: Specific value
    test_value = 0x0F00000000000000;
    expected_result = 4;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 5 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    // Test case 6: Another specific value
    test_value = 0x00000000000000F0;
    expected_result = 56;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 6 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    // Test case 7: Value with some leading zeros
    test_value = 0x00FF00FF00FF00FF;
    expected_result = 8;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 7 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    // Test case 8: Value close to max
    test_value = std::numeric_limits<bits64>::max() - 1;
    expected_result = 0;
    actual_result = countLeadingZeros64(test_value);
    if (actual_result != expected_result) {
        std::cerr << "Test Case 8 Failed: Input = " << test_value
                  << ", Expected = " << (int)expected_result
                  << ", Actual = " << (int)actual_result << std::endl;
        fail_flag = 1;
    }

    if (fail_flag == 0) {
        std::cout << "All test cases passed!" << std::endl;
    } else {
        std::cout << "Some test cases failed." << std::endl;
    }

    return fail_flag;
}