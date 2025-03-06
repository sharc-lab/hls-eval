#include <iostream>

#include "check_clockwise.h"

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
    int test_failed = 0;

    // Test case 1: Clockwise triangle
    Triangle_2D t1 = {0, 0, 2, 0, 1, 1, 0};
    int result_0 = check_clockwise(t1);
    if (result_0 >= 0) {
        std::cout << "Test 1 failed!\n";
        std::cout << "Expected negative, got " << result_0 << std::endl;
        print_triangle(t1);
        test_failed = 1;
    }

    // Test case 2: Counterclockwise triangle
    Triangle_2D t2 = {0, 0, 1, 1, 2, 0, 0};
    int result_1 = check_clockwise(t2);
    if (result_1 <= 0) {
        std::cout << "Test 2 failed!\n";
        std::cout << "Expected positive, got " << result_1 << std::endl;
        print_triangle(t2);
        test_failed = 1;
    }

    // Test case 3: Collinear points (should be zero)
    Triangle_2D t3 = {0, 0, 1, 1, 2, 2, 0};
    int result_2 = check_clockwise(t3);
    if (result_2 != 0) {
        std::cout << "Test 3 failed!\n";
        std::cout << "Expected zero, got " << result_2 << std::endl;
        print_triangle(t3);
        test_failed = 1;
    }

    // Test case 4: Another clockwise triangle
    Triangle_2D t4 = {3, 3, 6, 2, 4, 5, 0};
    int result_3 = check_clockwise(t4);
    if (result_3 >= 0) {
        std::cout << "Test 4 failed!\n";
        std::cout << "Expected negative, got " << result_3 << std::endl;
        print_triangle(t4);
        test_failed = 1;
    }

    // Test case 5: Another counterclockwise triangle
    Triangle_2D t5 = {3, 3, 4, 5, 6, 2, 0};
    int result_4 = check_clockwise(t5);
    if (result_4 <= 0) {
        std::cout << "Test 5 failed!\n";
        std::cout << "Expected positive, got " << result_4 << std::endl;
        print_triangle(t5);
        test_failed = 1;
    }

    return test_failed;
}