## aes_aes

An implementation of AES-256 encryption in Electronic Codebook (ECB) mode. The kernel performs the encryption operation on a 16-byte block of data using a 256-bit key. The design is byte-oriented, meaning it operates on individual bytes of the data and key, and all lookup tables have been replaced with on-the-fly calculations.

Top-Level Function: `aes256_encrypt_ecb`

Inputs:

- `ctx`: a pointer to an `aes256_context` structure, which contains the encryption key and other necessary information
- `k`: a 32-byte array containing the 256-bit encryption key
- `buf`: a 16-byte array containing the plaintext data to be encrypted

Outputs:

- `buf`: the encrypted 16-byte array

Important Data Structures and Data Types:

- `aes256_context`: a structure containing the encryption key, encryption key schedule, and decryption key schedule
- `uint8_t`: an unsigned 8-bit integer type used to represent individual bytes of data and key

Sub-Components:

- `aes_subBytes`: a function that substitutes each byte of the data with a corresponding byte from the S-box
- `aes_addRoundKey`: a function that adds the round key to the data
- `aes_shiftRows`: a function that shifts the rows of the data matrix
- `aes_mixColumns`: a function that mixes the columns of the data matrix
- `aes_expandEncKey`: a function that expands the encryption key schedule
- `rj_sbox`: a function that calculates the S-box value for a given byte
- `rj_xtime`: a function that calculates the xtime value for a given byte
- `gf_alog` and `gf_log`: functions that calculate the anti-logarithm and logarithm, respectively, in the Galois field
- `gf_mulinv`: a function that calculates the multiplicative inverse in the Galois field