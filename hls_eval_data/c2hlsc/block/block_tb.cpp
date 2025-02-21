
int main() {
    int i;
    for (i = 0; i < N * M; i++) {
        epsilon[i] = i * 73 % 7 == 0;
    }
    double result;
    BlockFrequency(&result);

    printf("result = %f\n", result);
}
