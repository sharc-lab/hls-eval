#include <cstdio>

#include "outer_product.h"

gradient_t test_gradient[MAX_HEIGHT][MAX_WIDTH];
outer_t test_output[MAX_HEIGHT][MAX_WIDTH];

int main() {

    // Initialize test input
    for (int r = 0; r < MAX_HEIGHT; r++) {
        for (int c = 0; c < MAX_WIDTH; c++) {
            test_gradient[r][c].x = (pixel_t)(r * MAX_WIDTH + c);
            test_gradient[r][c].y = (pixel_t)(-r * MAX_WIDTH + c / 2);
            test_gradient[r][c].z = (pixel_t)(r * MAX_WIDTH + c / 2);
        }
    }

    // Run the function under test∆
    outer_product(test_gradient, test_output);

    // Verify output
    bool pass = true;
    for (int r = 0; r < MAX_HEIGHT; r++) {
        for (int c = 0; c < MAX_WIDTH; c++) {
            pixel_t x = test_gradient[r][c].x;
            pixel_t y = test_gradient[r][c].y;
            pixel_t z = test_gradient[r][c].z;
            outer_pixel_t expected_val[6] = {(outer_pixel_t)(x * x),
                                             (outer_pixel_t)(y * y),
                                             (outer_pixel_t)(z * z),
                                             (outer_pixel_t)(x * y),
                                             (outer_pixel_t)(x * z),
                                             (outer_pixel_t)(y * z)};

            for (int i = 0; i < 6; i++) {
                if (test_output[r][c].val[i] != expected_val[i]) {
                    printf("Mismatch at (%d, %d) index %d\n", r, c, i);
                    printf(
                        "Expected: %d, Got: %d\n",
                        expected_val[i],
                        test_output[r][c].val[i]);
                    if (i == 0) {
                        printf("x: %d\n", x);
                        printf("computed: x * x\n");
                    } else if (i == 1) {
                        printf("y: %d\n", y);
                        printf("computed: y * y\n");
                    } else if (i == 2) {
                        printf("z: %d\n", z);
                        printf("computed: z * z\n");
                    } else if (i == 3) {
                        printf("x: %d, y: %d\n", x, y);
                        printf("computed: x * y\n");
                    } else if (i == 4) {
                        printf("x: %d, z: %d\n", x, z);
                        printf("computed: x * z\n");
                    } else if (i == 5) {
                        printf("y: %d, z: %d\n", y, z);
                        printf("computed: y * z\n");
                    }
                    pass = false;
                }
            }
        }
    }

    if (pass) {
        printf("Test Passed!\n");
        return 0;
    } else {
        printf("Test Failed!\n");
        return 1;
    }
}
