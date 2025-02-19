#pragma once
#include <cmath>

void kernel_fdtd_2d(
    double ex[20 + 0][30 + 0],
    double ey[20 + 0][30 + 0],
    double hz[20 + 0][30 + 0],
    double _fict_[20 + 0]);
