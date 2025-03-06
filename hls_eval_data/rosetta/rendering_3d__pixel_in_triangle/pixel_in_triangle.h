#include "ap_int.h"

typedef ap_uint<1> bit1;
typedef ap_uint<8> bit8;

// struct: 2D triangle
typedef struct {
    bit8 x0;
    bit8 y0;
    bit8 x1;
    bit8 y1;
    bit8 x2;
    bit8 y2;
    bit8 z;
} Triangle_2D;

bit1 pixel_in_triangle(bit8 x, bit8 y, Triangle_2D triangle_2d);