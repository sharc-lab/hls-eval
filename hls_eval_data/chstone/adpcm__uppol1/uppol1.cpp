#include "uppol1.h"

/* uppol1 - update first predictor coefficient (pole section) */
/* inputs: al1, apl2, plt, plt1. outputs: apl1 */
int uppol1(int al1, int apl2, int plt, int plt1) {
    long int wd2;
    int wd3, apl1;
    wd2 = ((long)al1 * 255L) >> 8L; /* leak factor of 255/256 */
    if ((long)plt * plt1 >= 0L) {
        apl1 = (int)wd2 + 192; /* same sign case */
    } else {
        apl1 = (int)wd2 - 192;
    }
    /* note: wd3= .9375-.75 is always positive */
    wd3 = 15360 - apl2; /* limit value */
    if (apl1 > wd3)
        apl1 = wd3;
    if (apl1 < -wd3)
        apl1 = -wd3;
    return (apl1);
}