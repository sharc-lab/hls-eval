#include "float64_abs.h"

float64 float64_abs(float64 x) { return (x & 0x7fffffffffffffffULL); }