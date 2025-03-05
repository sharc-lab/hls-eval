#pragma once
#include <cmath>

void kernel_2mm(
    double alpha,
    double beta,
    double tmp[16][18],
    double A[16][22],
    double B[22][18],
    double C[18][24],
    double D[16][24]);
