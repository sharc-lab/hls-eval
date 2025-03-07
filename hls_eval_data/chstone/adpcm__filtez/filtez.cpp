#include "filtez.h"

/* filtez - compute predictor output signal (zero section) */
/* input: bpl1-6 and dlt1-6, output: szl */
int filtez(int *bpl, int *dlt) {
    int i;
    long int zl;
    zl = (long)(*bpl++) * (*dlt++);
    for (i = 1; i < 6; i++)
        zl += (long)(*bpl++) * (*dlt++);

    return ((int)(zl >> 14)); /* x2 here */
}