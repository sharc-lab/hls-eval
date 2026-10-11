#include <memory.h>
#include <stdio.h>

#include "des.h"

static void fixture_des_key_setup(
    const unsigned char key[],
    des_key_t schedule,
    DES_MODE mode) {
    unsigned int i, j, to_gen, C, D;
    const unsigned int key_rnd_shift[16] = {
        1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1};
    const unsigned int key_perm_c[28] = {56, 48, 40, 32, 24, 16, 8,  0,  57, 49,
                                         41, 33, 25, 17, 9,  1,  58, 50, 42, 34,
                                         26, 18, 10, 2,  59, 51, 43, 35};
    const unsigned int key_perm_d[28] = {62, 54, 46, 38, 30, 22, 14, 6,  61, 53,
                                         45, 37, 29, 21, 13, 5,  60, 52, 44, 36,
                                         28, 20, 12, 4,  27, 19, 11, 3};
    const unsigned int key_compression[48] = {
        13, 16, 10, 23, 0,  4,  2,  27, 14, 5,  20, 9,  22, 18, 11, 3,
        25, 7,  15, 6,  26, 19, 12, 1,  40, 51, 30, 36, 46, 54, 29, 39,
        50, 44, 32, 47, 43, 48, 38, 55, 33, 52, 45, 41, 49, 35, 28, 31};

    // Permutated Choice #1 (copy the key in, ignoring parity bits).
    for (i = 0, j = 31, C = 0; i < 28; ++i, --j)
        C |= BITNUM(key, key_perm_c[i], j);
    for (i = 0, j = 31, D = 0; i < 28; ++i, --j)
        D |= BITNUM(key, key_perm_d[i], j);

    // Generate the 16 subkeys.
    for (i = 0; i < 16; ++i) {
        C = ((C << key_rnd_shift[i]) | (C >> (28 - key_rnd_shift[i]))) &
            0xfffffff0;
        D = ((D << key_rnd_shift[i]) | (D >> (28 - key_rnd_shift[i]))) &
            0xfffffff0;

        // Decryption subkeys are reverse order of encryption subkeys so
        // generate them in reverse if the key schedule is for decryption
        // useage.
        if (mode == DES_DECRYPT)
            to_gen = 15 - i;
        else /*(if mode == DES_ENCRYPT)*/
            to_gen = i;
        // Initialize the array
        for (j = 0; j < 6; ++j)
            schedule[to_gen][j] = 0;
        for (j = 0; j < 24; ++j)
            schedule[to_gen][j / 8] |=
                BITNUMINTR(C, key_compression[j], 7 - (j % 8));
        for (; j < 48; ++j)
            schedule[to_gen][j / 8] |=
                BITNUMINTR(D, key_compression[j] - 28, 7 - (j % 8));
    }
}


int main() {
    des_block_t pt1 = {0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xE7};
    unsigned char key1[DES_BLOCK_SIZE] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF};

    des_key_t schedule;
    des_block_t buf;

    fixture_des_key_setup(key1, schedule, DES_ENCRYPT);
    des_crypt(&pt1, &buf, &schedule);

    for (int i = 0; i < 8; i++)
        printf("%02X ", buf[i]);

    return 0;
}
