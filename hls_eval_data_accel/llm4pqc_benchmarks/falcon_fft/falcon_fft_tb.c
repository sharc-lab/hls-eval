#include "falcon_fft.h"
#include "vectors.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
int main(void) {
    double a[512];
    for (int i=0;i<512;++i) a[i]=input[i];
    falcon_fft(a);
    for(int i=0;i<512;++i) {
        if(!isfinite(a[i]) || fabs(a[i]-expected[i])>1e-7+1e-10*fabs(expected[i])) {
            fprintf(stderr,"Mismatch at %d\n",i); return 1;
        }
    }
    puts("falcon_fft: PASS"); return 0;
}
