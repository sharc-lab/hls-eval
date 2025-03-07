#include "upzero.h"

/* upzero - inputs: dlt, dlti[0-5], bli[0-5], outputs: updated bli[0-5] */
/* also implements delay of bli and update of dlti from dlt */

void upzero(int dlt, int *dlti, int *bli) {
    int i, wd2, wd3;
    /*if dlt is zero, then no sum into bli */
    if (dlt == 0) {
        for (i = 0; i < 6; i++) {
            bli[i] = (int)((255L * bli[i]) >> 8L); /* leak factor of 255/256 */
        }
    } else {
        for (i = 0; i < 6; i++) {
            if ((long)dlt * dlti[i] >= 0)
                wd2 = 128;
            else
                wd2 = -128;
            wd3 = (int)((255L * bli[i]) >> 8L); /* leak factor of 255/256 */
            bli[i] = wd2 + wd3;
        }
    }
    /* implement delay line for dlt */
    dlti[5] = dlti[4];
    dlti[4] = dlti[3];
    dlti[3] = dlti[2];
    dlti[2] = dlti[1];
    dlti[1] = dlti[0];
    dlti[0] = dlt;
}
