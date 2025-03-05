#include <stdint.h>

#include <stdio.h>
#include <stdlib.h>

#define FFT_SIZE 1024
#define twoPI 6.28318530717959

void fft(
    double real[FFT_SIZE],
    double img[FFT_SIZE],
    double real_twid[FFT_SIZE / 2],
    double img_twid[FFT_SIZE / 2]);
