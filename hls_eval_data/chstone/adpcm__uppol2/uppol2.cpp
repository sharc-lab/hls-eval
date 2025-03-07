#include "uppol2.h"

/* uppol2 - update second predictor coefficient (pole section) */
/* inputs: al1, al2, plt, plt1, plt2. outputs: apl2 */

int uppol2(int al1, int al2, int plt, int plt1, int plt2) {
    long int wd2, wd4;
    int apl2;
    wd2 = 4L * (long)al1;
    if ((long)plt * plt1 >= 0L)
        wd2 = -wd2; /* check same sign */
    wd2 = wd2 >> 7; /* gain of 1/128 */
    if ((long)plt * plt2 >= 0L) {
        wd4 = wd2 + 128; /* same sign case */
    } else {
        wd4 = wd2 - 128;
    }
    apl2 = wd4 + (127L * (long)al2 >> 7L); /* leak factor of 127/128 */

    /* apl2 is limited to +-.75 */
    if (apl2 > 12288)
        apl2 = 12288;
    if (apl2 < -12288)
        apl2 = -12288;
    return (apl2);
}