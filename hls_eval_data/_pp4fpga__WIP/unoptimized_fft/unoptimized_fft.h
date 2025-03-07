#include "hls_math.h"

typedef float DTYPE;
typedef int INTTYPE;
#define M 10            /* Number of Stages = Log2N */
#define SIZE 1024       /* SIZE OF FFT */
#define SIZE2 SIZE >> 1 /* SIZE/2 */

void fft(DTYPE XX_R[SIZE], DTYPE XX_I[SIZE]);