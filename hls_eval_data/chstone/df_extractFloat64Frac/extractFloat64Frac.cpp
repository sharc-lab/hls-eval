#include "extractFloat64Frac.h"

bits64 extractFloat64Frac(float64 a) { return a & 0x000FFFFFFFFFFFFFLL; }