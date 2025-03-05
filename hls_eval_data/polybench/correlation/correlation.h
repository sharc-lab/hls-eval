#pragma once
#include <cmath>

void kernel_correlation(
    double float_n,
    double data[32][28],
    double corr[28][28],
    double mean[28],
    double stddev[28]);
