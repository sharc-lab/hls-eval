#include <stdio.h>

#define N 20000
static int epsilon[N]; // array of 0s and 1s

void CumulativeSums(int *res_sup, int *res_inf);