#include "logsch.h"

/* logsch - update log quantizer scale factor in higher sub-band */
/* note that nbh is passed and returned */
int logsch(int ih, int nbh) {
    int wd;
    wd = ((long)nbh * 127L) >> 7L; /* leak factor 127/128 */
    nbh = wd + wh_code_table[ih];
    if (nbh < 0)
        nbh = 0;
    if (nbh > 22528)
        nbh = 22528;
    return (nbh);
}