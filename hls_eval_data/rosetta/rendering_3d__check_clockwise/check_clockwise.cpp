#include "check_clockwise.h"

int check_clockwise(Triangle_2D triangle_2d) {
    int cw;

    cw = (triangle_2d.x2 - triangle_2d.x0) * (triangle_2d.y1 - triangle_2d.y0) -
         (triangle_2d.y2 - triangle_2d.y0) * (triangle_2d.x1 - triangle_2d.x0);

    return cw;
}
