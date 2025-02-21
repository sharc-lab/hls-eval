Description:
The `present80_encryptBlock` kernel represents a high-level synthesis design for encrypting a block of data using the PRESENT-80 encryption algorithm. The design consists of several sub-components that work together to perform the encryption process.

Top-Level Function: `present80_encryptBlock`
Complete Function Signature: `void present80_encryptBlock(block_t *block, present_key_t *key);`

Inputs:
- `block`: a pointer to a block of data to be encrypted, represented as an array of 8 unsigned char values (block_t *).
- `key`: a pointer to the encryption key, represented as an array of 10 unsigned char values (present_key_t *).

Outputs:
- None

Important Data Structures and Data Types:
- `block_t`: a data structure representing a block of data, consisting of 8 unsigned char values.
- `present_key_t`: a data structure representing the encryption key, consisting of 10 unsigned char values.
- `keys_t`: a data structure representing an array of round keys, consisting of ROUNDS (32) arrays of 8 unsigned char values each.
- `round_key_t`: a data structure representing a round key, consisting of 8 unsigned char values.
- `sBox`: a lookup table used for substitution in the encryption process, consisting of 16 unsigned char values.
- `sBoxInverse`: a lookup table used for inverse substitution in the decryption process, consisting of 16 unsigned char values.

Sub-Components:
- `generateRoundKeys80`: generates the round keys for the encryption process.
- `addRoundKey`: adds a round key to the block of data.
- `pLayer`: performs the p-layer operation on the block of data.
- `pLayerInverse`: performs the inverse p-layer operation on the block of data.
- `copyKey`: copies the contents of one key to another.
- `copyBlock`: copies the contents of one block to another.