Description:
The AddRoundKey kernel is a high-level synthesis (HLS) implementation of the AddRoundKey function from the Advanced Encryption Standard (AES) algorithm. The function takes a round number, a state array, and a round key as inputs, and updates the state array by adding the round key to it using an XOR operation. The round key is added to the state array in a specific pattern, where each element of the state array is XORed with the corresponding element of the round key.

Top-Level Function: `AddRoundKey`
Complete Function Signature: `void AddRoundKey(uint8_t round, state_t *state, const uint8_t *RoundKey);`

Inputs:
- `round`: The current round number, represented as a uint8_t.
- `state`: A pointer to a 4x4 state array, represented as a state_t.
- `RoundKey`: A pointer to a round key array, represented as a const uint8_t.

Outputs:
- None

Important Data Structures and Data Types:
- `state_t`: A 4x4 array of uint8_t, representing the state array.
- `uint8_t`: An 8-bit unsigned integer, used to represent the round number and the elements of the state array and round key.

Sub-Components:
- None