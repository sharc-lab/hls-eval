#include"lc_gicov.h"

// ap_fixed has no NaN/Inf representation, so a divisor that quantizes to
// exactly 0 (which the float baseline silently turns into NaN/Inf) would
// otherwise abort the C-sim; fall back to 0 for the ap_fixed conversion.
static inline fixed_t safe_div(fixed_t a, fixed_t b) {
  if (b == fixed_t(0)) return fixed_t(0);
  return fixed_t(a / b);
}

extern "C" {

void workload(fixed_t result[GRID_ROWS * GRID_COLS], fixed_t grad_x[GRID_ROWS * GRID_COLS], fixed_t grad_y[GRID_ROWS * GRID_COLS])
{

    #pragma HLS INTERFACE m_axi port=result offset=slave bundle=gmem
    #pragma HLS INTERFACE m_axi port=grad_x offset=slave bundle=gmem
    #pragma HLS INTERFACE m_axi port=grad_y offset=slave bundle=gmem
    
    #pragma HLS INTERFACE s_axilite port=result bundle=control
    #pragma HLS INTERFACE s_axilite port=grad_x bundle=control
    #pragma HLS INTERFACE s_axilite port=grad_y bundle=control
    
    #pragma HLS INTERFACE s_axilite port=return bundle=control

    fixed_t sin_angle[16] = {0, 0.382683432365090, 0.707106781186548, 0.923879532511287, 1, 0.923879532511287, 0.707106781186548, 0.382683432365090, 1.22464679914735e-16, -0.382683432365090, -0.707106781186548, -0.923879532511287, -1, -0.923879532511287, -0.707106781186548, -0.382683432365090};

    fixed_t cos_angle[16] = {1, 0.923879532511287, 0.707106781186548, 0.382683432365090, 6.12323399573677e-17, -0.382683432365090, -0.707106781186548, -0.923879532511287, -1, -0.923879532511287, -0.707106781186548, -0.382683432365090, -1.83697019872103e-16, 0.382683432365090, 0.707106781186547, 0.923879532511287};

    int tX[2][16] = {{1, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1, 0, 0, 0, 0}, {2, 1, 1, 0, 0, -1, -2, -2, -2, -2, -2, -1, 0, 0, 1, 1}};

    int tY[2][16] = {{0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1, -1}, {0, 0, 1, 1, 1, 1, 1, 0, 0, -1, -2, -2, -2, -2, -2, -1}};

    int i, n, k;

	// Allocate memory for the result matrix
	// int GRID_ROWS = GRID_ROWS, GRID_COLS = GRID_COLS;
	fixed_t *gicov = (fixed_t*)malloc(GRID_ROWS * GRID_COLS * sizeof(fixed_t));


	// Scan from left to right, top to bottom, computing GICOV values
	for (i = MAX_RADIUS; i < GRID_COLS - MAX_RADIUS; i++) {
		fixed_t Grad[NPOINTS];
		int j, k, n, x, y;

		for (j = MAX_RADIUS; j < GRID_ROWS - MAX_RADIUS; j++) {
			// Initialize the maximal GICOV score to 0
			fixed_t max_GICOV = 0;

			// Iterate across each stencil
			for (k = 0; k < NCIRCLES; k++) {
				// Iterate across each sample point in the current stencil
				for (n = 0; n < NPOINTS; n++) {
					// Determine the x- and y-coordinates of the current sample point
					y = j + tY[k][n];
					x = i + tX[k][n];

					// Compute the combined gradient value at the current sample point
					Grad[n] = grad_x[y * GRID_COLS + x] * cos_angle[n] + grad_y[y * GRID_COLS + x] * sin_angle[n];
				}

				// Compute the mean gradient value across all sample points
				fixed_t sum = 0.0;
				for (n = 0; n < NPOINTS; n++) sum += Grad[n];
				fixed_t mean = sum / (fixed_t)NPOINTS;

				// Compute the variance of the gradient values
				fixed_t var = 0.0;
				for (n = 0; n < NPOINTS; n++) {
					sum = Grad[n] - mean;
					var += sum * sum;
				}
				var = var / (fixed_t)(NPOINTS - 1);

				// Keep track of the maximal GICOV value seen so far
				fixed_t gicov_val = safe_div(mean * mean, var);
				if (gicov_val > max_GICOV) {
					fixed_t stddev = fixed_t(sqrt((double)var));
					result[j * GRID_COLS + i] = safe_div(mean, stddev);
					max_GICOV = gicov_val;
				}
			}
		}
	}
    
	return;
}

}

