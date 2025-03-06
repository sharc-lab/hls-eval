#include <iostream>

#include "pixel_in_triangle.h"

void print_triangle(Triangle_2D triangle) {
    printf(
        "Triangle: (%d, %d), (%d, %d), (%d, %d) z=%d\n",
        triangle.x0,
        triangle.y0,
        triangle.x1,
        triangle.y1,
        triangle.x2,
        triangle.y2,
        triangle.z);
}

int main() {
    int fail_flag = 0;

    // Define test cases
    Triangle_2D triangle1 = {0, 0, 10, 0, 5, 10, 1}; // Right-angled triangle

    // Points inside
    bit1 result_0 = pixel_in_triangle(5, 5, triangle1);
    bit1 result_1 = pixel_in_triangle(3, 2, triangle1);

    fail_flag |= (result_0 != 1);
    fail_flag |= (result_1 != 1);

    if (result_0 != 1) {
        std::cout << "Error: incorrect result_0: " << result_0 << std::endl;
        std::cout << "Expected: 1" << std::endl;
        std::cout << "point: x=5, y=5" << std::endl;
        print_triangle(triangle1);
    }
    if (result_1 != 1) {
        std::cout << "Error: incorrect result_1: " << result_1 << std::endl;
        std::cout << "Expected: 1" << std::endl;
        std::cout << "point: x=3, y=2" << std::endl;
        print_triangle(triangle1);
    }

    // Points on edges
    bit1 result_2 = pixel_in_triangle(0, 0, triangle1);
    bit1 result_3 = pixel_in_triangle(10, 0, triangle1);
    bit1 result_4 = pixel_in_triangle(5, 10, triangle1);

    fail_flag |= (result_2 != 1);
    fail_flag |= (result_3 != 1);
    fail_flag |= (result_4 != 1);

    if (result_2 != 1) {
        std::cout << "Error: incorrect result_2: " << result_2 << std::endl;
        std::cout << "Expected: 1" << std::endl;
        std::cout << "point: x=0, y=0" << std::endl;
        print_triangle(triangle1);
    }

    if (result_3 != 1) {
        std::cout << "Error: incorrect result_3: " << result_3 << std::endl;
        std::cout << "Expected: 1" << std::endl;
        std::cout << "point: x=10, y=0" << std::endl;
        print_triangle(triangle1);
    }

    if (result_4 != 1) {
        std::cout << "Error: incorrect result_4: " << result_4 << std::endl;
        std::cout << "Expected: 1" << std::endl;
        std::cout << "point: x=5, y=10" << std::endl;
        print_triangle(triangle1);
    }

    // Points outside
    bit1 result_5 = pixel_in_triangle(11, 5, triangle1);
    bit1 result_6 = pixel_in_triangle(6, 11, triangle1);
    bit1 result_7 = pixel_in_triangle(-1, 0, triangle1);

    fail_flag |= (result_5 != 0);
    fail_flag |= (result_6 != 0);
    fail_flag |= (result_7 != 0);

    if (result_5 != 0) {
        std::cout << "Error: incorrect result_5: " << result_5 << std::endl;
        std::cout << "Expected: 0" << std::endl;
        std::cout << "point: x=11, y=5" << std::endl;
        print_triangle(triangle1);
    }

    if (result_6 != 0) {
        std::cout << "Error: incorrect result_6: " << result_6 << std::endl;
        std::cout << "Expected: 0" << std::endl;
        std::cout << "point: x=6, y=11" << std::endl;
        print_triangle(triangle1);
    }

    if (result_7 != 0) {
        std::cout << "Error: incorrect result_7: " << result_7 << std::endl;
        std::cout << "Expected: 0" << std::endl;
        std::cout << "point: x=-1, y=0" << std::endl;
        print_triangle(triangle1);
    }

    if (fail_flag) {
        std::cout << "Test failed!" << std::endl;
    } else {
        std::cout << "Test passed!" << std::endl;
    }

    return fail_flag;
}