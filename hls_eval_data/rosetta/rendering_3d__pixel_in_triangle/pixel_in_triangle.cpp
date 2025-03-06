#include "pixel_in_triangle.h"

bit1 pixel_in_triangle(bit8 x, bit8 y, Triangle_2D triangle_2d) {

    int pi0, pi1, pi2;

    pi0 = (x - triangle_2d.x0) * (triangle_2d.y1 - triangle_2d.y0) -
          (y - triangle_2d.y0) * (triangle_2d.x1 - triangle_2d.x0);
    pi1 = (x - triangle_2d.x1) * (triangle_2d.y2 - triangle_2d.y1) -
          (y - triangle_2d.y1) * (triangle_2d.x2 - triangle_2d.x1);
    pi2 = (x - triangle_2d.x2) * (triangle_2d.y0 - triangle_2d.y2) -
          (y - triangle_2d.y2) * (triangle_2d.x0 - triangle_2d.x2);

    return (pi0 >= 0 && pi1 >= 0 && pi2 >= 0) ||
           (pi0 <= 0 && pi1 <= 0 && pi2 <= 0);
}