#include "clockwise_vertices.h"

void clockwise_vertices(Triangle_2D *triangle_2d) {

    bit8 tmp_x, tmp_y;

    tmp_x = triangle_2d->x0;
    tmp_y = triangle_2d->y0;

    triangle_2d->x0 = triangle_2d->x1;
    triangle_2d->y0 = triangle_2d->y1;

    triangle_2d->x1 = tmp_x;
    triangle_2d->y1 = tmp_y;
}