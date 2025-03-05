#pragma once
#include <cmath>

void kernel_3mm(
    double E[16][18],
    double A[16][20],
    double B[20][18],
    double F[18][22],
    double C[18][24],
    double D[24][22],
    double G[16][22]);
