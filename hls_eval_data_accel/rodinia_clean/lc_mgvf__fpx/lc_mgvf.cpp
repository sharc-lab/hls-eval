#include"lc_mgvf.h"

extern "C" {

fixed_t heaviside(fixed_t x) {
    // A simpler, faster approximation of the Heaviside function
    fixed_t out = 0.0;
    if (x > -0.0001) out = 0.5;
    if (x >  0.0001) out = 1.0;
    return out; 
}

fixed_t lc_mgvf(fixed_t result[GRID_ROWS * GRID_COLS], fixed_t imgvf[GRID_ROWS * GRID_COLS], fixed_t I[GRID_ROWS * GRID_COLS])
{
    fixed_t total_diff = 0.0;

    for (int i = 0; i < GRID_ROWS; i++) {
        for (int j = 0; j < GRID_COLS; j++) {
            fixed_t old_val = imgvf[i * GRID_COLS + j];

            fixed_t UL    = ((i == 0              ||  j == 0              ) ? fixed_t(0) : fixed_t(imgvf[(i - 1   ) * GRID_COLS + (j - 1  )] - old_val));
            fixed_t U     = ((i == 0                                      ) ? fixed_t(0) : fixed_t(imgvf[(i - 1   ) * GRID_COLS + (j      )] - old_val));
            fixed_t UR    = ((i == 0              ||  j == GRID_COLS - 1  ) ? fixed_t(0) : fixed_t(imgvf[(i - 1   ) * GRID_COLS + (j + 1  )] - old_val));

            fixed_t L     = ((                        j == 0              ) ? fixed_t(0) : fixed_t(imgvf[(i       ) * GRID_COLS + (j - 1  )] - old_val));
            fixed_t R     = ((                        j == GRID_COLS - 1  ) ? fixed_t(0) : fixed_t(imgvf[(i       ) * GRID_COLS + (j + 1  )] - old_val));

            fixed_t DL    = ((i == GRID_ROWS - 1  ||  j == 0              ) ? fixed_t(0) : fixed_t(imgvf[(i + 1   ) * GRID_COLS + (j - 1  )] - old_val));
            fixed_t D     = ((i == GRID_ROWS - 1                          ) ? fixed_t(0) : fixed_t(imgvf[(i + 1   ) * GRID_COLS + (j      )] - old_val));
            fixed_t DR    = ((i == GRID_ROWS - 1  ||  j == GRID_COLS - 1  ) ? fixed_t(0) : fixed_t(imgvf[(i + 1   ) * GRID_COLS + (j + 1  )] - old_val));

            fixed_t vHe = old_val + fixed_t(MU_O_LAMBDA) * (heaviside(UL) * UL + heaviside(U) * U + heaviside(UR) * UR + heaviside(L) * L + heaviside(R) * R + heaviside(DL) * DL + heaviside(D) * D + heaviside(DR) * DR);

            fixed_t vI = I[i * GRID_COLS + j];
            fixed_t new_val = vHe - (fixed_t(ONE_O_LAMBDA) * vI * (vHe - vI));
            result[i * GRID_COLS + j] = new_val;

            total_diff += fixed_t(fabs((double)(new_val - old_val)));
        }
    }

    return (total_diff / (fixed_t)(GRID_ROWS * GRID_COLS));
}

void workload(fixed_t result[GRID_ROWS * GRID_COLS], fixed_t imgvf[GRID_ROWS * GRID_COLS], fixed_t I[GRID_ROWS * GRID_COLS])
{
    #pragma HLS INTERFACE m_axi port=result offset=slave bundle=result1
    #pragma HLS INTERFACE m_axi port=imgvf offset=slave bundle=imgvf1
    #pragma HLS INTERFACE m_axi port=I offset=slave bundle=I1
    
    #pragma HLS INTERFACE s_axilite port=result bundle=control
    #pragma HLS INTERFACE s_axilite port=imgvf bundle=control
    #pragma HLS INTERFACE s_axilite port=I bundle=control
    
    #pragma HLS INTERFACE s_axilite port=return bundle=control

    int i;
    fixed_t diff = 1.0;
    for (i = 0; i < ITERATION / 2; i++) {
        diff = lc_mgvf(result, imgvf, I);
        diff = lc_mgvf(imgvf, result, I);
    }
    return;

}








}
