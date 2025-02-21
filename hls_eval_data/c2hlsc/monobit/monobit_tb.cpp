#include "monobit.h"

int main() {
    int i;
    for (i = 0; i < N; i++) {
        epsilon[i] = i * 73 % 7 == 0;
    }
    int result;
    Frequency(&result);

    printf("result = %d\n", result);
}