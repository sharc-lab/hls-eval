int main() {
    int i;
    for (i = 0; i < N; i++) {
        epsilon[i] = i * 73 % 7 == 0;
    }
    double result;
    Overlapping(&result);

    printf("result = %.0f\n", result);
}