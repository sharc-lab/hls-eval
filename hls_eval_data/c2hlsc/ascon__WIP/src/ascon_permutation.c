#include <stdint.h>
#include "ascon_permutation.h"


#define ROTATE_RIGHT(x, i) (((x) >> (i)) | ((x) << (64 - (i))))

void round_i(uint64_t *state, uint8_t round);
void s_box_layer(uint64_t *state, uint64_t *t);
void diffusion_layer(uint64_t *state, uint64_t *t);


const uint8_t round_constants[12] = {
    0xf0, 0xe1, 0xd2, 0xc3, 0xb4, 0xa5,
    0x96, 0x87, 0x78, 0x69, 0x5a, 0x4b
};

void permute_a(uint64_t *state)
{
    uint8_t i;
    for (i = 0; i < N_ROUNDS_A; i++)
	round_i(state, i);
}

void permute_b(uint64_t *state)
{
    uint64_t i;
    for (i = 0; i < N_ROUNDS_B; i++)
	round_i(state, i + 6);
}

void round_i(uint64_t *state, uint8_t round)
{
    uint64_t temp[5];
    state[2] ^= round_constants[round];
    s_box_layer(state, temp);
    diffusion_layer(state, temp);
}

void s_box_layer(uint64_t *state, uint64_t *t)
{
    state[0] ^= state[4];
    state[4] ^= state[3];
    state[2] ^= state[1];

    t[0] = state[0] ^ (~state[1] & state[2]);
    t[1] = state[1] ^ (~state[2] & state[3]);
    t[2] = state[2] ^ (~state[3] & state[4]);
    t[3] = state[3] ^ (~state[4] & state[0]);
    t[4] = state[4] ^ (~state[0] & state[1]);

    t[1] ^= t[0];
    t[0] ^= t[4];
    t[3] ^= t[2];
    t[2] = ~t[2];
}

void diffusion_layer(uint64_t *state, uint64_t *t)
{
    state[0] = t[0] ^ ROTATE_RIGHT(t[0], 19) ^ ROTATE_RIGHT(t[0], 28);
    state[1] = t[1] ^ ROTATE_RIGHT(t[1], 61) ^ ROTATE_RIGHT(t[1], 39);
    state[2] = t[2] ^ ROTATE_RIGHT(t[2], 1) ^ ROTATE_RIGHT(t[2], 6);
    state[3] = t[3] ^ ROTATE_RIGHT(t[3], 10) ^ ROTATE_RIGHT(t[3], 17);
    state[4] = t[4] ^ ROTATE_RIGHT(t[4], 7) ^ ROTATE_RIGHT(t[4], 41);
}
