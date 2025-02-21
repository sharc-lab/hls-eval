Description:
The SubBytes kernel is a high-level synthesis (HLS) design that implements the SubBytes function of the Advanced Encryption Standard (AES) algorithm. The SubBytes function is responsible for substituting the values in the state matrix with values from an S-box. The S-box is a pre-defined table of 256 bytes, where each byte is a substitution value for a corresponding input byte.

Top-Level Function: `SubBytes`
Complete Function Signature: `void SubBytes(state_t *state);`

Inputs:
- `state`: a 4x4 matrix of 8-bit unsigned integers, representing the state matrix to be substituted.

Outputs:
- None

Important Data Structures and Data Types:
- `state_t`: a 2D array of 8-bit unsigned integers, representing the state matrix.
- `uint8_t`: an 8-bit unsigned integer data type.
- `sbox`: a pre-defined table of 256 bytes, representing the S-box.

Sub-Components:
- `getSBoxValue(num)`: a function that returns the substitution value for a given input byte from the S-box.
- `phex(str)`: a function that prints a hexadecimal representation of a byte array.