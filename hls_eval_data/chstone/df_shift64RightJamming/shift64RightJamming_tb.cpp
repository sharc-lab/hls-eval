#include "shift64RightJamming.h"
#include <stdio.h>

// Define a structure to hold test cases
typedef struct {
    bits64 a;                // Input value
    int16 count;             // Shift count
    bits64 expected_z;       // Expected output
    const char *description; // Description of the test case
} TestCase;

int main() {
    int8 test_result = 0;

    TestCase test_cases[] = {
        {0x123456789ABCDEF0, 0, 0x123456789ABCDEF0, "Test case 1: count = 0"},
        {0x123456789ABCDEF0, 4, 0x0123456789ABCDEF, "Test case 2: count < 64"},
        {0x123456789ABCDEF0, 64, 0x1, "Test case 3: count >= 64"},
        {0x0, 8, 0x0, "Test case 4: count < 64, zero input"},
        {0x8000000000000001,
         1,
         0x4000000000000001,
         "Test case 5: count < 64, specific pattern for jamming"}};

    int num_test_cases = sizeof(test_cases) / sizeof(test_cases[0]);

    for (int i = 0; i < num_test_cases; i++) {
        bits64 z;
        shift64RightJamming(test_cases[i].a, test_cases[i].count, &z);

        // Check if the output matches the expected value
        if (z != test_cases[i].expected_z) {
            printf(
                "%s failed: expected 0x%llx, got 0x%llx\n",
                test_cases[i].description,
                test_cases[i].expected_z,
                z);
            test_result = 1; // Mark test as failed
        } else {
            printf("%s passed\n", test_cases[i].description);
        }
    }

    // Print final result
    if (test_result == 0) {
        printf("All test cases passed!\n");
    } else {
        printf("Some test cases failed!\n");
    }

    return test_result;
}