Description:
The DES (Data Encryption Standard) is a symmetric-key block cipher that was widely used for encrypting data. The DES algorithm is a Feistel cipher, which means it uses a series of rounds to encrypt the data. Each round consists of a substitution step, followed by a permutation step. The DES algorithm uses a 56-bit key, which is reduced to 48 bits after the key expansion process.

Top-Level Function: `des_crypt`
Complete Function Signature: `void des_crypt(des_block_t *in, des_block_t *out, des_key_t *key);`

Inputs:
- `in`: the input block to be encrypted or decrypted
- `out`: the output block after encryption or decryption
- `key`: the DES key schedule

Outputs:
- `out`: the encrypted or decrypted block

Important Data Structures and Data Types:
- `des_block_t`: a 64-bit block of data
- `des_key_t`: a 16x6 array of 32-bit words, representing the DES key schedule
- `des_state_t`: a 2x32 array of 32-bit words, representing the DES state

Sub-Components:
- `IP`: the initial permutation function, which rearranges the bits of the input block
- `InvIP`: the inverse initial permutation function, which rearranges the bits of the output block
- `f`: the DES round function, which performs the substitution and permutation steps
- `des_key_setup`: the key setup function, which expands the DES key from 56 bits to 48 bits