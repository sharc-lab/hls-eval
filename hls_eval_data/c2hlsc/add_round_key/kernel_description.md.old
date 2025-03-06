Kernel Description:
The AddRoundKey kernel is a high-level synthesis design that implements the AddRoundKey function from the Advanced Encryption Standard (AES) algorithm. The function takes three inputs: the current round number, a state matrix, and a round key. The function adds the round key to the state matrix using an XOR operation. The state matrix is a 4x4 matrix of 8-bit unsigned integers, and the round key is an array of 176 8-bit unsigned integers.

Top-Level Function: `AddRoundKey`
Complete Function Signature: `void AddRoundKey(uint8_t round, state_t *state, const uint8_t *RoundKey);`

Inputs:
- `round`: The current round number, represented as an 8-bit unsigned integer.
- `state`: A pointer to a 4x4 matrix of 8-bit unsigned integers, representing the current state of the AES algorithm.
- `RoundKey`: A pointer to an array of 176 8-bit unsigned integers, representing the current round key.

Outputs:
- None

Important Data Structures and Data Types:
- `state_t`: A 4x4 matrix of 8-bit unsigned integers, representing the current state of the AES algorithm.
- `uint8_t`: An 8-bit unsigned integer, used to represent the elements of the state matrix and the round key.

Sub-Components:
- None