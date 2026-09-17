#pragma once
#include <stdint.h>
int falcon_sampler(double mu, double isigma, double sigma_min, uint8_t buf[512], uint64_t ptr[1], uint8_t state[256]);
