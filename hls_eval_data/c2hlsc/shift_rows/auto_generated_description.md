Description:
The ShiftRows() function is a high-level synthesis (HLS) kernel that implements the ShiftRows operation from the Advanced Encryption Standard (AES) algorithm. The function takes a 4x4 state matrix as input and shifts the rows of the matrix to the left according to a specific offset. The offset is determined by the row number, with the first row not being shifted. The function is designed to be highly optimized for parallel processing and is intended for implementation on a hardware accelerator.

Top-Level Function: `ShiftRows`
Complete Function Signature: `void ShiftRows(state_t *state);`

Inputs:
- `state`: a 4x4 state matrix of type `state_t`, where each element is an 8-bit unsigned integer (uint8_t)

Outputs:
- None

Important Data Structures and Data Types:
- `state_t`: a 4x4 matrix of 8-bit unsigned integers (uint8_t), representing the state of the AES algorithm
- `uint8_t`: an 8-bit unsigned integer type, used to represent the elements of the state matrix

Sub-Components:
- `temp`: a temporary variable of type `uint8_t`, used to store intermediate values during the shifting operation
- `state`: the input 4x4 state matrix, accessed through a pointer of type `state_t *`