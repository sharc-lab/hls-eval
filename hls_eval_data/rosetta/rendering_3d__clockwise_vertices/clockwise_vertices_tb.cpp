#include <cstdio>

#include "clockwise_vertices.h"

int main() {
    Triangle_2D triangle_2d;

    // Test case 1
    triangle_2d.x0 = 1;
    triangle_2d.y0 = 2;
    triangle_2d.x1 = 3;
    triangle_2d.y1 = 4;
    triangle_2d.x2 = 5;
    triangle_2d.y2 = 6;
    triangle_2d.z = 7;

    clockwise_vertices(&triangle_2d);

    if (triangle_2d.x0 != 3 || triangle_2d.y0 != 4 || triangle_2d.x1 != 1 ||
        triangle_2d.y1 != 2) {
        printf("Test failed for triangle_2d\n");
        printf("Expected: x0=3, y0=4, x1=1, y1=2\n");
        printf(
            "Got: x0=%d, y0=%d, x1=%d, y1=%d\n",
            triangle_2d.x0,
            triangle_2d.y0,
            triangle_2d.x1,
            triangle_2d.y1);

        return 1;
    }

    // Test case 2
    triangle_2d.x0 = 10;
    triangle_2d.y0 = 20;
    triangle_2d.x1 = 30;
    triangle_2d.y1 = 40;
    triangle_2d.x2 = 50;
    triangle_2d.y2 = 60;
    triangle_2d.z = 70;

    clockwise_vertices(&triangle_2d);

    if (triangle_2d.x0 != 30 || triangle_2d.y0 != 40 || triangle_2d.x1 != 10 ||
        triangle_2d.y1 != 20) {
        printf("Test failed for triangle_2d\n");
        printf("Expected: x0=30, y0=40, x1=10, y1=20\n");
        printf(
            "Got: x0=%d, y0=%d, x1=%d, y1=%d\n",
            triangle_2d.x0,
            triangle_2d.y0,
            triangle_2d.x1,
            triangle_2d.y1);
        return 1;
    }

    return 0;
}