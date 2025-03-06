
#include "extractFloat64Exp.h"

int16 extractFloat64Exp(float64 a) { return (a >> 52) & 0x7FF; }