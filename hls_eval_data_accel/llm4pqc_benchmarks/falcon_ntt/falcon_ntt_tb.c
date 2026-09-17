#include "falcon_ntt.h"
#include "vectors.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
int main(void) {
    uint16_t a[1024];
    for (int i=0;i<1024;++i) a[i]=input[i];
    falcon_ntt(a);
    for (int i=0;i<1024;++i) {
        int64_t v=a[i]; v%= 12289; if(v<0) v+=12289;
        if(v!=expected[i]) { fprintf(stderr,"Mismatch at %d\n",i); return 1; }
    }
    puts("falcon_ntt: PASS"); return 0;
}
