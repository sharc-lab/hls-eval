#pragma once
#include <cmath>

void kernel_gemm(
    double alpha,
    double beta,
    double C[20 + 0][25 + 0],
    double A[20 + 0][30 + 0],
    double B[30 + 0][25 + 0]);
