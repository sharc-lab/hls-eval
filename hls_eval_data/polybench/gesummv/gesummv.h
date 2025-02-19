#pragma once
#include <cmath>

void kernel_gesummv(
    double alpha,
    double beta,
    double A[30 + 0][30 + 0],
    double B[30 + 0][30 + 0],
    double tmp[30 + 0],
    double x[30 + 0],
    double y[30 + 0]);
