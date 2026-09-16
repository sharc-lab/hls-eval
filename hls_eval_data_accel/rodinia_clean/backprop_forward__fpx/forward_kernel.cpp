#include <math.h>
#include <string.h>
#include "ap_fixed.h"
typedef ap_fixed<32, 16> fixed_t;
#define ETA 0.3       //eta value
#define TILE_SIZE 512

extern "C" {
void workload(fixed_t l1[65537], fixed_t l2[17], fixed_t conn[65537 * 17]) {
#pragma HLS INTERFACE m_axi port=l1 offset=slave bundle=l11
#pragma HLS INTERFACE m_axi port=l2 offset=slave bundle=l21
#pragma HLS INTERFACE m_axi port=conn offset=slave bundle=conn1


#pragma HLS INTERFACE s_axilite port=l1 bundle=control
#pragma HLS INTERFACE s_axilite port=l2 bundle=control
#pragma HLS INTERFACE s_axilite port=conn bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

    fixed_t sum;
    int j, k, kk;
    fixed_t l1_buf[65537];
    fixed_t conn_buf[TILE_SIZE*17];
    fixed_t l2_buf[17];

    memcpy(l1_buf, l1, sizeof(fixed_t) * 65537);

    /*** Set up thresholding unit ***/
    l1_buf[0] = 1.0;

    /*** For each unit in second layer ***/
    for (j = 1; j <= 16; j++) {
        /*** Compute weighted sum of its inputs ***/
        sum = 0.0;

        for (kk = 0; kk < 65536 + TILE_SIZE; kk += TILE_SIZE) {
            int size = (kk == 65536)?1:TILE_SIZE;
            memcpy(conn_buf, conn+kk*17, sizeof(fixed_t) * size * 17);
            for (k = 0; k < TILE_SIZE; k++) {
                if (k + kk < 65537) {
                    fixed_t product = conn_buf[k * 17 + j] * l1_buf[k + kk];
                    sum += product;
                }
            }
        }
        
        l2_buf[j] = fixed_t(1.0) / (fixed_t(1.0) + fixed_t(exp(-(double)sum)));
    }
    memcpy(l2, l2_buf, sizeof(fixed_t) * 17);
}
}
