#include <ap_int.h>

ap_int<32> dot4(const ap_int<16> a[4], const ap_int<16> b[4]) {
    ap_int<32> result = 0;
    for (int i = 0; i < 4; ++i) {
        result += a[i] * b[i];
    }
    return result;
}
