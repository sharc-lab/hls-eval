Description:
The `present80_encryptBlock` kernel is a high-level synthesis design that implements the PRESENT-80 encryption algorithm. The algorithm is a lightweight block cipher designed for low-power and high-speed applications. The kernel takes a plaintext block and a key as input, and produces a ciphertext block as output.

Top-Level Function: `present80_encryptBlock`
Complete Function Signature: `void present80_encryptBlock(block_t *block, present_key_t *key);`

Inputs:
- `block`: a pointer to a `block_t` structure, representing the plaintext block to be encrypted. The `block_t` structure is an array of 8 unsigned char elements, representing the 64-bit plaintext block.
- `key`: a pointer to a `present_key_t` structure, representing the encryption key. The `present_key_t` structure is an array of 10 unsigned char elements, representing the 80-bit encryption key.

Outputs:
- `block`: the encrypted ciphertext block, stored in the same `block_t` structure as the input plaintext block.

Important Data Structures and Data Types:
- `block_t`: a structure representing a 64-bit plaintext or ciphertext block, consisting of an array of 8 unsigned char elements.
- `present_key_t`: a structure representing an 80-bit encryption key, consisting of an array of 10 unsigned char elements.
- `keys_t`: a structure representing an array of round keys, consisting of an array of `ROUNDS` (32) elements, each element being an array of 8 unsigned char elements.
- `round_key_t`: a structure representing a single round key, consisting of an array of 8 unsigned char elements.
- `sBox`: a lookup table used in the encryption algorithm, consisting of 16 unsigned char elements.

Sub-Components:
- `generateRoundKeys80`:
    - Signature: `void generateRoundKeys80(present_key_t *suppliedKey, keys_t *keys);`
    - Details: This function generates the round keys for the encryption algorithm. It takes the supplied key and generates the round keys using a series of bitwise operations and table lookups.
- `addRoundKey`:
    - Signature: `void addRoundKey(block_t *block, round_key_t *roundKey);`
    - Details: This function adds the round key to the plaintext block. It takes the plaintext block and the round key as input, and produces the encrypted block as output.
- `pLayer`:
    - Signature: `void pLayer(block_t *block);`
    - Details: This function applies the p-layer transformation to the plaintext block. It takes the plaintext block as input, and produces the transformed block as output.
- `pLayerInverse`:
    - Signature: `void pLayerInverse(block_t *block);`
    - Details: This function applies the inverse p-layer transformation to the ciphertext block. It takes the ciphertext block as input, and produces the transformed block as output.