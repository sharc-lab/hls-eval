#include <iostream>

#include "projection.h"

void print_triangle_2d(Triangle_2D triangle) {
    printf(
        "Triangle 2d: (%d, %d), (%d, %d), (%d, %d) z=%d\n",
        triangle.x0,
        triangle.y0,
        triangle.x1,
        triangle.y1,
        triangle.x2,
        triangle.y2,
        triangle.z);
}

void print_triangle_3d(Triangle_3D triangle) {
    printf(
        "Triangle 3d: (%d, %d, %d), (%d, %d, %d), (%d, %d, %d)\n",
        triangle.x0,
        triangle.y0,
        triangle.z0,
        triangle.x1,
        triangle.y1,
        triangle.z1,
        triangle.x2,
        triangle.y2,
        triangle.z2);
}

// Function to compare two 2D triangles
bool compare_triangles(const Triangle_2D &t1, const Triangle_2D &t2) {
    return t1.x0 == t2.x0 && t1.y0 == t2.y0 && t1.x1 == t2.x1 &&
           t1.y1 == t2.y1 && t1.x2 == t2.x2 && t1.y2 == t2.y2 && t1.z == t2.z;
}

// Testbench for the projection function
int main() {
    int test_failures = 0;

    // Test Case 1: Angle = 0
    {
        Triangle_3D triangle_3d = {10, 20, 30, 40, 50, 60, 70, 80, 90};
        Triangle_2D triangle_2d_expected = {
            10, 20, 40, 50, 70, 80, (30 / 3) + (60 / 3) + (90 / 3)};
        Triangle_2D triangle_2d_actual;

        projection(triangle_3d, &triangle_2d_actual, 0);

        if (!compare_triangles(triangle_2d_actual, triangle_2d_expected)) {
            std::cout << "Test Case 1 Failed!" << std::endl;
            std::cout << "Expected: ";
            print_triangle_2d(triangle_2d_expected);
            std::cout << "Actual: ";
            print_triangle_2d(triangle_2d_actual);
            std::cout << "Original 3D triangle: ";
            print_triangle_3d(triangle_3d);
            std::cout << "Angle: 0" << std::endl;
            test_failures++;
        }
    }

    // Test Case 2: Angle = 1
    {
        Triangle_3D triangle_3d = {10, 20, 30, 40, 50, 60, 70, 80, 90};
        Triangle_2D triangle_2d_expected = {
            10, 30, 40, 60, 70, 90, (20 / 3) + (50 / 3) + (80 / 3)};
        Triangle_2D triangle_2d_actual;

        projection(triangle_3d, &triangle_2d_actual, 1);

        if (!compare_triangles(triangle_2d_actual, triangle_2d_expected)) {
            std::cout << "Test Case 2 Failed!" << std::endl;
            std::cout << "Expected: ";
            print_triangle_2d(triangle_2d_expected);
            std::cout << "Actual: ";
            print_triangle_2d(triangle_2d_actual);
            std::cout << "Original 3D triangle: ";
            print_triangle_3d(triangle_3d);
            std::cout << "Angle: 1" << std::endl;
            test_failures++;
        }
    }

    // Test Case 3: Angle = 2
    {
        Triangle_3D triangle_3d = {10, 20, 30, 40, 50, 60, 70, 80, 90};
        Triangle_2D triangle_2d_expected = {
            30, 20, 60, 50, 90, 80, (10 / 3) + (40 / 3) + (70 / 3)};
        Triangle_2D triangle_2d_actual;

        projection(triangle_3d, &triangle_2d_actual, 2);

        if (!compare_triangles(triangle_2d_actual, triangle_2d_expected)) {
            std::cout << "Test Case Failed!" << std::endl;
            std::cout << "Expected: ";
            print_triangle_2d(triangle_2d_expected);
            std::cout << "Actual: ";
            print_triangle_2d(triangle_2d_actual);
            std::cout << "Original 3D triangle: ";
            print_triangle_3d(triangle_3d);
            std::cout << "Angle: 2" << std::endl;
            test_failures++;
        }
    }

    // Test Case 4: Edge case with zero coordinates
    {
        Triangle_3D triangle_3d = {0, 0, 0, 0, 0, 0, 0, 0, 0};
        Triangle_2D triangle_2d_expected = {0, 0, 0, 0, 0, 0, 0};
        Triangle_2D triangle_2d_actual;

        projection(triangle_3d, &triangle_2d_actual, 0);

        if (!compare_triangles(triangle_2d_actual, triangle_2d_expected)) {
            std::cout << "Test Case 4 Failed!" << std::endl;
            std::cout << "Expected: ";
            print_triangle_2d(triangle_2d_expected);
            std::cout << "Actual: ";
            print_triangle_2d(triangle_2d_actual);
            std::cout << "Original 3D triangle: ";
            print_triangle_3d(triangle_3d);
            std::cout << "Angle: 0" << std::endl;
            test_failures++;
        }
    }

    {
        Triangle_3D triangle_3d = {255, 255, 255, 255, 255, 255, 255, 255, 255};
        Triangle_2D triangle_2d_expected = {255, 255, 255, 255, 255, 255, 255};
        Triangle_2D triangle_2d_actual;

        projection(triangle_3d, &triangle_2d_actual, 0);

        if (!compare_triangles(triangle_2d_actual, triangle_2d_expected)) {
            std::cout << "Test Case 5 Failed!" << std::endl;
            std::cout << "Expected: ";
            print_triangle_2d(triangle_2d_expected);
            std::cout << "Actual: ";
            print_triangle_2d(triangle_2d_actual);
            std::cout << "Original 3D triangle: ";
            print_triangle_3d(triangle_3d);
            std::cout << "Angle: 0" << std::endl;
            test_failures++;
        }
    }

    // Summary of test results
    if (test_failures == 0) {
        std::cout << "All test cases passed!" << std::endl;
        return 0;
    } else {
        std::cout << test_failures << " test case(s) failed!" << std::endl;
        return 1;
    }
}