#include "dfdiv.h"

int8 float_rounding_mode = 0;
int8 float_exception_flags = 0;

void float_raise(int8 flags) { float_exception_flags |= flags; }