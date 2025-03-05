#pragma once
#include <cmath>

void kernel_fdtd_2d(
    double ex[20][30],
    double ey[20][30],
    double hz[20][30],
    double _fict_[20]);
