#include <cstdlib>
#include <iostream>

#include "vec_add.h"

int main() {
    int in0[VEC_ADD_N];
    int in1[VEC_ADD_N];
    int out[VEC_ADD_N];

    for (int i = 0; i < VEC_ADD_N; i++) {
        in0[i] = i;
        in1[i] = 2 * i;
    }

    vec_add(in0, in1, out);

    for (int i = 0; i < VEC_ADD_N; i++) {
        int expected = in0[i] + in1[i];
        if (out[i] != expected) {
            std::cerr << "Mismatch at index " << i << ": expected " << expected
                       << ", got " << out[i] << std::endl;
            return EXIT_FAILURE;
        }
    }

    std::cout << "Test passed!" << std::endl;
    return EXIT_SUCCESS;
}
