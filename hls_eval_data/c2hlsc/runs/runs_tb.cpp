#include "runs.h"

int main() {
    int i;
    for (i = 0; i < N; i++) {
        epsilon[i] = i * 73 % 7 == 0;
    }
    int result_S, result_V;
    Runs(&result_S, &result_V);

    printf("result S = %d\n", result_S);
    printf("result S = %d\n", result_V);
}
