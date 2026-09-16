#include"hotspot.h"

// ap_fixed<32,16> has only ~1.5e-5 resolution; hotspot's SI-unit physical
// constants (Cap ~4e-7, Rx/Ry denominators ~3e-6) underflow to exactly 0 at
// this width, causing a genuine divide-by-zero trap in the scalar precompute
// chain below. Guard those divisions the same way as the other __fpx designs.
static inline fixed_t safe_div(fixed_t a, fixed_t b) {
  if (b == fixed_t(0)) return fixed_t(0);
  return fixed_t(a / b);
}

extern"C" {

void hotspot(fixed_t result[GRID_ROWS * GRID_COLS], fixed_t temp[GRID_ROWS * GRID_COLS], fixed_t power[GRID_ROWS * GRID_COLS], fixed_t Cap_1, fixed_t Rx_1, fixed_t Ry_1, fixed_t Rz_1) {
    fixed_t amb_temp = 80.0;
    fixed_t delta;

    for (int r = 0; r < GRID_ROWS; r++)
        for (int c = 0; c < GRID_COLS; c++) {
            if (r == 0 || c == 0 || r == GRID_ROWS - 1 || c == GRID_COLS - 1) {

                /* Corner 1 */
                if ((r == 0) && (c == 0)) {
                    delta = (Cap_1) * (power[0] +
                        (temp[1] - temp[0]) * Rx_1 +
                        (temp[GRID_COLS] - temp[0]) * Ry_1 +
                        (amb_temp - temp[0]) * Rz_1);
                }   
    
                /* Corner 2 */
                else if ((r == 0) && (c == GRID_COLS - 1)) {
                    delta = (Cap_1) * (power[c] +
                        (temp[c - 1] - temp[c]) * Rx_1 +
                        (temp[c + GRID_COLS] - temp[c]) * Ry_1 +
                        (amb_temp - temp[c]) * Rz_1);
                }   
    
                /* Corner 3 */
                else if ((r == GRID_ROWS - 1) && (c == GRID_COLS - 1)) {
                    delta = (Cap_1) * (power[r*GRID_COLS + c] +
                        (temp[r*GRID_COLS + c - 1] - temp[r*GRID_COLS + c]) * Rx_1 +
                        (temp[(r - 1)*GRID_COLS + c] - temp[r*GRID_COLS + c]) * Ry_1 +
                        (amb_temp - temp[r*GRID_COLS + c]) * Rz_1);
                }   
    
                /* Corner 4 */
                else if ((r == GRID_ROWS - 1) && (c == 0)) {
                    delta = (Cap_1) * (power[r*GRID_COLS] +
                        (temp[r*GRID_COLS + 1] - temp[r*GRID_COLS]) * Rx_1 +
                        (temp[(r - 1)*GRID_COLS] - temp[r*GRID_COLS]) * Ry_1 +
                        (amb_temp - temp[r*GRID_COLS]) * Rz_1);
                }   
    
                /* Edge 1 */
                else if (r == 0) {
                    delta = (Cap_1) * (power[c] +
                        (temp[c + 1] + temp[c - 1] - fixed_t(2.0)*temp[c]) * Rx_1 +
                        (temp[GRID_COLS + c] - temp[c]) * Ry_1 +
                        (amb_temp - temp[c]) * Rz_1);
                }   
    
                /* Edge 2 */
                else if (c == GRID_COLS - 1) {
                    delta = (Cap_1) * (power[r*GRID_COLS + c] +
                        (temp[(r + 1)*GRID_COLS + c] + temp[(r - 1)*GRID_COLS + c] - fixed_t(2.0)*temp[r*GRID_COLS + c]) * Ry_1 +
                        (temp[r*GRID_COLS + c - 1] - temp[r*GRID_COLS + c]) * Rx_1 +
                        (amb_temp - temp[r*GRID_COLS + c]) * Rz_1);
                }   
    
                /* Edge 3 */
                else if (r == GRID_ROWS - 1) {
                    delta = (Cap_1) * (power[r*GRID_COLS + c] +
                        (temp[r*GRID_COLS + c + 1] + temp[r*GRID_COLS + c - 1] - fixed_t(2.0)*temp[r*GRID_COLS + c]) * Rx_1 +
                        (temp[(r - 1)*GRID_COLS + c] - temp[r*GRID_COLS + c]) * Ry_1 +
                        (amb_temp - temp[r*GRID_COLS + c]) * Rz_1);
                }   
    
                /* Edge 4 */
                else if (c == 0) {
                    delta = (Cap_1) * (power[r*GRID_COLS] +
                        (temp[(r + 1)*GRID_COLS] + temp[(r - 1)*GRID_COLS] - fixed_t(2.0)*temp[r*GRID_COLS]) * Ry_1 +
                        (temp[r*GRID_COLS + 1] - temp[r*GRID_COLS]) * Rx_1 +
                        (amb_temp - temp[r*GRID_COLS]) * Rz_1);
                }

            }

            else {
                    delta = (Cap_1 * (power[r*GRID_COLS + c] +
                        (temp[(r + 1)*GRID_COLS + c] + temp[(r - 1)*GRID_COLS + c] - fixed_t(2.0)*temp[r*GRID_COLS + c]) * Ry_1 +
                        (temp[r*GRID_COLS + c + 1] + temp[r*GRID_COLS + c - 1] - fixed_t(2.0)*temp[r*GRID_COLS + c]) * Rx_1 +
                        (amb_temp - temp[r*GRID_COLS + c]) * Rz_1));
            }

            result[r*GRID_COLS + c] = temp[r*GRID_COLS + c] + delta;

        }

    return;
}




void workload(fixed_t result[GRID_ROWS * GRID_COLS], fixed_t temp[GRID_ROWS * GRID_COLS], fixed_t power[GRID_ROWS * GRID_COLS])
{

    #pragma HLS INTERFACE m_axi port=result offset=slave bundle=gmem
    #pragma HLS INTERFACE m_axi port=temp offset=slave bundle=gmem
    #pragma HLS INTERFACE m_axi port=power offset=slave bundle=gmem
    
    #pragma HLS INTERFACE s_axilite port=result bundle=control
    #pragma HLS INTERFACE s_axilite port=temp bundle=control
    #pragma HLS INTERFACE s_axilite port=power bundle=control
    
    #pragma HLS INTERFACE s_axilite port=return bundle=control
    
    fixed_t grid_height = CHIP_HEIGHT / GRID_ROWS;
    fixed_t grid_width = CHIP_WIDTH / GRID_COLS;

    fixed_t Cap = fixed_t(FACTOR_CHIP * SPEC_HEAT_SI * T_CHIP) * grid_width * grid_height;
    fixed_t Rx = safe_div(grid_width, fixed_t(2.0 * K_SI * T_CHIP) * grid_height);
    fixed_t Ry = safe_div(grid_height, fixed_t(2.0 * K_SI * T_CHIP) * grid_width);
    fixed_t Rz = safe_div(fixed_t(T_CHIP), fixed_t(K_SI) * grid_height * grid_width);

    fixed_t max_slope = safe_div(fixed_t(MAX_PD), fixed_t(FACTOR_CHIP * T_CHIP * SPEC_HEAT_SI));
    fixed_t step = safe_div(safe_div(fixed_t(PRECISION), max_slope), fixed_t(1000.0));

    fixed_t Rx_1 = safe_div(fixed_t(1.0), Rx);
    fixed_t Ry_1 = safe_div(fixed_t(1.0), Ry);
    fixed_t Rz_1 = safe_div(fixed_t(1.0), Rz);
    fixed_t Cap_1 = safe_div(step, Cap);

    int i;
    for (i = 0; i < SIM_TIME/2; i++) {
       hotspot(result, temp, power, Cap_1, Rx_1, Ry_1, Rz_1);
       
       hotspot(temp, result, power, Cap_1, Rx_1, Ry_1, Rz_1);

    }

    return;
}

}
