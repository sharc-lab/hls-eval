#include "scalel.h"

/* scalel: compute quantizer scale factor in lower or upper sub-band*/
int scalel(int nbl, int shift_constant) {
    int wd1, wd2, wd3;
    wd1 = (nbl >> 6) & 31;
    wd2 = nbl >> 11;
    wd3 = ilb_table[wd1] >> (shift_constant + 1 - wd2);
    return (wd3 << 3);
}