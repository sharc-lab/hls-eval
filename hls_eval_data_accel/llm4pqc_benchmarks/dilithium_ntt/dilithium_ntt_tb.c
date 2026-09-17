#include "dilithium_ntt.h"
#include "vectors.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
int main(void) {
    int32_t a[256];
    for (int i=0;i<256;++i) a[i]=input[i];
    dilithium_ntt(a);
    for (int i=0;i<256;++i) {
        int64_t v=a[i]; v%= 8380417; if(v<0) v+=8380417;
        if(v!=expected[i]) { fprintf(stderr,"Mismatch at %d\n",i); return 1; }
    }
    puts("dilithium_ntt: PASS"); return 0;
}
