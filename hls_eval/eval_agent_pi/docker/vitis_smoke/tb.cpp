#include <ap_int.h>
#include <cstdio>

ap_int<32> dot4(const ap_int<16> a[4], const ap_int<16> b[4]);

int main() {
    const ap_int<16> a[4] = {1, -2, 3, 4};
    const ap_int<16> b[4] = {5, 6, -7, 8};
    const int result = dot4(a, b).to_int();
    if (result != 4) {
        std::printf("FAIL: expected 4, got %d\n", result);
        return 1;
    }
    std::puts("PASS: dot4 = 4");
    return 0;
}
