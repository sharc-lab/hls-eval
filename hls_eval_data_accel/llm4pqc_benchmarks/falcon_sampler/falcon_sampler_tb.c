#include "falcon_sampler.h"
#include "vectors.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
int main(void) {
    uint8_t buf[512],state[256]; uint64_t ptr[1]={initial_ptr[0]};
    memcpy(buf,initial_buf,512); memcpy(state,initial_state,256);
    for(int i=0;i<20;++i) {
        int sample=falcon_sampler(mu[i],isigma[i],sigma_min,buf,ptr,state);
        if(sample!=expected[i]) { fprintf(stderr,"Mismatch at draw %d\n",i); return 1; }
    }
    if(memcmp(buf,final_buf,512) || memcmp(state,final_state,256) || ptr[0]!=final_ptr[0]) {
        fprintf(stderr,"PRNG state mismatch\n"); return 1;
    }
    puts("falcon_sampler: PASS"); return 0;
}
