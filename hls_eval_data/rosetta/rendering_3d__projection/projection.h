#include "ap_int.h"

typedef ap_uint<2> bit2;
typedef ap_uint<8> bit8;

// struct: 3D triangle
typedef struct {
    bit8 x0;
    bit8 y0;
    bit8 z0;
    bit8 x1;
    bit8 y1;
    bit8 z1;
    bit8 x2;
    bit8 y2;
    bit8 z2;
} Triangle_3D;

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

void projection(Triangle_3D triangle_3d, Triangle_2D *triangle_2d, bit2 angle);
