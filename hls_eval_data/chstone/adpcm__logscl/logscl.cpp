#include "logscl.h"

/* logscl - update log quantizer scale factor in lower sub-band */
/* note that nbl is passed and returned */

int logscl(int il, int nbl) {
    long int wd;
    wd = ((long)nbl * 127L) >> 7L; /* leak factor 127/128 */
    nbl = (int)wd + wl_code_table[il >> 2];
    if (nbl < 0)
        nbl = 0;
    if (nbl > 18432)
        nbl = 18432;
    return (nbl);
}