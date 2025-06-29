#include <stdint.h>

/*
 *   Byte-oriented AES-256 implementation.
 *   All lookup tables replaced with 'on the fly' calculations.
 */

typedef struct {
    uint8_t key[32];
    uint8_t enckey[32];
    uint8_t deckey[32];
} aes256_context;

void aes256_encrypt_ecb(aes256_context *ctx, uint8_t k[32], uint8_t buf[16]);