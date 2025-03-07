/* decision levels - pre-multiplied by 8, 0 to indicate end */
static const int decis_levl[30] = {
    280,  576,   880,   1200,  1520,  1864,  2208,  2584,  2960,  3376,
    3784, 4240,  4696,  5200,  5712,  6288,  6864,  7520,  8184,  8968,
    9752, 10712, 11664, 12896, 14120, 15840, 17560, 20456, 23352, 32767};

/* quantization table 31 long to make quantl look-up easier,
last entry is for mil=30 case when wd is max */
static const int quant26bt_pos[31] = {
    61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46,
    45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 32};

/* quantization table 31 long to make quantl look-up easier,
last entry is for mil=30 case when wd is max */
static const int quant26bt_neg[31] = {
    63, 62, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18,
    17, 16, 15, 14, 13, 12, 11, 10, 9,  8,  7,  6,  5,  4,  4};

int quantl(int el, int detl);