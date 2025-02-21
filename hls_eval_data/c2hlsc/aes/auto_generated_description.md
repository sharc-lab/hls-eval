Description:
The AES (Advanced Encryption Standard) cipher is a block cipher that encrypts data in blocks of 128 bits. The cipher uses a variable-size key, typically 128, 192, or 256 bits, and operates on a 4x4 matrix of bytes, known as the state. The cipher consists of several rounds, each consisting of four operations: SubBytes, ShiftRows, MixColumns, and AddRoundKey. The SubBytes operation substitutes each byte of the state with a value from a lookup table, known as the S-box. The ShiftRows operation shifts the rows of the state to the left. The MixColumns operation mixes the columns of the state using a linear transformation. The AddRoundKey operation adds the round key to the state.

Top-Level Function: `Cipher`
Complete Function Signature of the Top-Level Function: `void Cipher(state_t *state, const round_t *RoundKey);`

Inputs:
- `state`: a 4x4 matrix of bytes representing the state of the cipher
- `RoundKey`: a 176-byte array representing the round key

Outputs:
- None

Important Data Structures and Data Types:
- `state_t`: a 4x4 matrix of bytes representing the state of the cipher
- `round_t`: a 176-byte array representing the round key
- `AES_ctx`: a struct containing the round key

Sub-Components:
- `KeyExpansion`: a function that expands the key into a series of round keys
- `AddRoundKey`: a function that adds the round key to the state
- `SubBytes`: a function that substitutes each byte of the state with a value from the S-box
- `ShiftRows`: a function that shifts the rows of the state to the left
- `MixColumns`: a function that mixes the columns of the state using a linear transformation
- `xtime`: a function that calculates the result of shifting a byte to the left and XORing it with a constant
- `getSBoxValue`: a function that returns the value of a byte in the S-box
- `Rcon`: a constant array of 11 bytes representing the round constants