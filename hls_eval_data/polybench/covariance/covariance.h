#pragma once
#include <cmath>

void kernel_covariance(
    double float_n,
    double data[32][28],
    double cov[28][28],
    double mean[28]);
