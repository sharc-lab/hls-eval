#include "update_knn.h"
#include <stdio.h>

int main() {
    WholeDigitType test_inst, train_inst;
    int min_distances[K_CONST];

    for (int i = 0; i < K_CONST; i++)
        min_distances[i] = 256;

    // Test Case 1: Identical instances (distance = 0)
    for (int i = 0; i < 256; i++) {
        test_inst[i] = 1;
        train_inst[i] = 1;
    }

    update_knn(test_inst, train_inst, min_distances);

    bool pass = false;
    for (int i = 0; i < K_CONST; i++)
        if (min_distances[i] == 0)
            pass = true;

    if (!pass) {
        printf("Test Case 1 Failed!\n");
        return 1;
    }

    // Test Case 2: Completely opposite instances (distance = 256)
    for (int i = 0; i < 256; i++) {
        test_inst[i] = 1;
        train_inst[i] = 0;
    }

    update_knn(test_inst, train_inst, min_distances);

    for (int i = 0; i < K_CONST; i++) {
        if (min_distances[i] == 256) {
            printf("Test Case 2 Failed!\n");
            return 1;
        }
    }

    // Test Case 3: Known small difference (distance = 1)
    for (int i = 0; i < 256; i++) {
        test_inst[i] = 0;
        train_inst[i] = 0;
    }

    test_inst[0] = 1;
    train_inst[0] = 0;

    update_knn(test_inst, train_inst, min_distances);

    pass = false;
    for (int i = 0; i < K_CONST; i++)
        if (min_distances[i] == 1)
            pass = true;

    if (!pass) {
        printf("Test Case 3 Failed!\n");
        return 1;
    }

    printf("All test cases passed!\n");
    return 0;
}
