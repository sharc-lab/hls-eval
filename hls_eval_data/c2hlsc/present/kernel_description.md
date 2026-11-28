Kernel Description:
The PRESENT-80 encryption algorithm is a lightweight block cipher designed for resource-constrained devices. It operates on64-bit blocks and uses an80-bit key. It uses31 substitution/permutation rounds with round-key addition, followed by a final key addition, using32 round keys. The substitution layer uses a 4-bit S-box to replace each nibble of the block, while the permutation layer rearranges the bits of the block. The key addition layer adds the round key to the block. The round keys are generated from the master key using a key schedule algorithm.

The key schedule algorithm generates 32 round keys from the 80-bit master key. It first copies the master key into the first round key, then applies a series of rotations, S-box substitutions, and XOR operations to generate the remaining round keys.

The encryption process starts by generating the round keys from the master key. Then, for each round, it adds the round key to the block, applies the substitution layer, and finally applies the permutation layer. After the last round, it adds the final round key to the block to produce the ciphertext.

The algorithm uses a number of constants and data structures, including the S-box, the master key, the round keys, and the block. The S-box is a 4-bit substitution table used in the substitution layer. The master key is the 80-bit key used to generate the round keys. The round keys are the 64-bit keys used in each round of the encryption process. The block is the 64-bit plaintext or ciphertext being encrypted or decrypted.

---

Top-Level Function: `present80_encryptBlock`

Complete Function Signature of the Top-Level Function:
`void present80_encryptBlock(block_t *block, present_key_t *key);`

Inputs:
- `block`: a pointer to a `block_t` array representing the 64-bit plaintext block to be encrypted. The block is stored in a byte array, with each byte representing 8 bits of the block.
- `key`: a pointer to a `present_key_t` array representing the 80-bit master key. The key is stored in a byte array, with each byte representing 8 bits of the key.

Outputs:
- The encrypted block is stored in the `block` array passed as input.

Important Data Structures and Data Types:
- `block_t`: a type representing a 64-bit block, stored as a byte array of length 8.
- `present_key_t`: a type representing a 80-bit key, stored as a byte array of length 10.
- `keys_t`: a type representing an array of 32 round keys, stored as a 2D byte array of size 32x8.
- `round_key_t`: a type representing a 64-bit round key, stored as a byte array of length 8.
- `sBox`: a 4-bit substitution table used in the substitution layer, stored as a byte array of length 16.

Sub-Components:
- `generateRoundKeys80`:
    - Signature: `void generateRoundKeys80(present_key_t *suppliedKey, keys_t *keys);`
    - Details: generates the 32 round keys from the master key using the key schedule algorithm.
- `addRoundKey`:
    - Signature: `void addRoundKey(block_t *block, round_key_t *roundKey);`
    - Details: adds the round key to the block.
- `pLayer`:
    - Signature: `void pLayer(block_t *block);`
    - Details: applies the permutation layer to the block.
- `copyKey`:
    - Signature: `void copyKey(present_key_t *from, present_key_t *to);`
    - Details: copies the master key from one location to another.
- `copyBlock`:
    - Signature: `void copyBlock(block_t *from, block_t *to);`
    - Details: copies the block from one location to another.
Complete PRESENT-80 convention:
Treat block bytes and key bytes as big-endian bit strings: byte0 is most significant. The supplied key is preserved. Round keys are the most significant64 bits of the current80-bit key, beginning with the supplied key. For key updates numbered1..31, rotate the80-bit key left61 bits, apply the header sBox to bits79..76, then XOR the five-bit update number into key bits19..15. Capture the next round key after each update.
For rounds1..31, XOR the corresponding round key into the block, apply the header sBox independently to each four-bit nibble, then permute bit b to position (16*b) mod63 for b<63 and preserve bit63. Bit0 is least significant. Finally XOR round key32. The only result is the eight updated block bytes.
ROUNDS=32 counts keys, not32 substitution/permutation applications.
