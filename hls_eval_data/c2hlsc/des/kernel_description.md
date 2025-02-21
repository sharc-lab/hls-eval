Description:
The DES (Data Encryption Standard) is a symmetric-key block cipher that was widely used for encrypting data. The design is based on the Feistel cipher structure, which is a type of block cipher that uses a substitution-permutation network (SPN) to encrypt data. The DES algorithm operates on 64-bit blocks of data, using a 56-bit key. The key is divided into 16 rounds, each consisting of a permutation and a substitution step. The permutation step rearranges the bits of the data block, while the substitution step replaces each bit with a different bit based on the current round key.

Top-Level Function: `des_crypt`
Complete Function Signature: `void des_crypt(des_block_t *in, des_block_t *out, des_key_t *key);`

Inputs:
- `in`: a pointer to the input block of data to be encrypted
- `out`: a pointer to the output block of data that will hold the encrypted result
- `key`: a pointer to the 56-bit key used for encryption

Outputs:
- `out`: the encrypted block of data

Important Data Structures and Data Types:
- `des_block_t`: a 64-bit block of data
- `des_key_t`: a 56-bit key used for encryption
- `des_state_t`: a 2-element array used to hold the intermediate state of the encryption process

Sub-Components:
- `IP`: the initial permutation step, which rearranges the bits of the input block
- `InvIP`: the inverse of the initial permutation step, which rearranges the bits of the output block
- `f`: the encryption function, which takes the current state and the current round key as input and produces the next state
- `des_key_setup`: a function that sets up the key schedule for the encryption process