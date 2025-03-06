Kernel Description:
The AES (Advanced Encryption Standard) is a widely used symmetric-key block cipher. The provided code implements the AES algorithm in C++. The AES algorithm consists of several rounds, each of which includes four main operations: SubBytes, ShiftRows, MixColumns, and AddRoundKey. The SubBytes operation applies a substitution table to each byte of the state matrix. The ShiftRows operation shifts the rows of the state matrix to the left. The MixColumns operation mixes the columns of the state matrix using a linear transformation. The AddRoundKey operation adds the round key to the state matrix.

Top-Level Function: `Cipher`
Complete Function Signature of the Top-Level Function: `void Cipher(state_t *state, const round_t *RoundKey);`

Inputs:
- `state`: a 4x4 state matrix representing the plaintext or ciphertext.
- `RoundKey`: a 176-byte round key.

Outputs:
- The function does not return any value, but it modifies the `state` matrix to represent the ciphertext.

Important Data Structures and Data Types:
- `state_t`: a 4x4 matrix of unsigned 8-bit integers, representing the state matrix.
- `round_t`: a 176-byte array of unsigned 8-bit integers, representing the round key.
- `AES_ctx`: a struct containing a 176-byte round key.

Sub-Components:
- `KeyExpansion`: a function that expands the key into a 176-byte round key.
- `AddRoundKey`: a function that adds the round key to the state matrix.
- `SubBytes`: a function that applies the substitution table to each byte of the state matrix.
- `ShiftRows`: a function that shifts the rows of the state matrix to the left.
- `MixColumns`: a function that mixes the columns of the state matrix using a linear transformation.
- `xtime`: a function that calculates the result of shifting a byte to the left and XORing it with a constant.