#include "filtep.h"

int filtep(int rlt1, int al1, int rlt2, int al2) {
    long int pl, pl2;
    pl = 2 * rlt1;
    pl = (long)al1 * pl;
    pl2 = 2 * rlt2;
    pl += (long)al2 * pl2;
    return ((int)(pl >> 15));
}