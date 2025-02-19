#pragma once
#include <cmath>

void kernel_covariance(
    double float_n,
    double data[32 + 0][28 + 0],
    double cov[28 + 0][28 + 0],
    double mean[28 + 0]);
