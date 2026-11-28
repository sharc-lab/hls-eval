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
            outer_pixel_t x = outer_pixel_t(pixel_t(r * MAX_WIDTH + c));
            outer_pixel_t y = outer_pixel_t(pixel_t(-r * MAX_WIDTH + c / 2));
            outer_pixel_t z = outer_pixel_t(pixel_t(r * MAX_WIDTH + c / 2));
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
                        "Expected: %g, Got: %g\n",
                        (double)expected_val[i],
                        (double)test_output[r][c].val[i]);
                    if (i == 0) {
                        printf("x: %g\n", (double)x);
                        printf("computed: x * x\n");
                    } else if (i == 1) {
                        printf("y: %g\n", (double)y);
                        printf("computed: y * y\n");
                    } else if (i == 2) {
                        printf("z: %g\n", (double)z);
                        printf("computed: z * z\n");
                    } else if (i == 3) {
                        printf("x: %g, y: %g\n", (double)x, (double)y);
                        printf("computed: x * y\n");
                    } else if (i == 4) {
                        printf("x: %g, z: %g\n", (double)x, (double)z);
                        printf("computed: x * z\n");
                    } else if (i == 5) {
                        printf("y: %g, z: %g\n", (double)y, (double)z);
                        printf("computed: y * z\n");
                    }
                    return 1; // One real mismatch suffices; passing still checks every field.
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
