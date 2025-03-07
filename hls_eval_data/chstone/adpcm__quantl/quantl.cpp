#include "quantl.h"

int abs(int n) { return (n >= 0) ? n : -n; }

/* quantl - quantize the difference signal in the lower sub-band */
int quantl(int el, int detl) {
    int ril, mil;
    long int wd, decis;

    /* abs of difference signal */
    wd = abs(el);
    /* determine mil based on decision levels and detl gain */
    for (mil = 0; mil < 30; mil++) {
        decis = (decis_levl[mil] * (long)detl) >> 15L;
        if (wd <= decis)
            break;
    }
    /* if mil=30 then wd is less than all decision levels */
    if (el >= 0)
        ril = quant26bt_pos[mil];
    else
        ril = quant26bt_neg[mil];
    return (ril);
}