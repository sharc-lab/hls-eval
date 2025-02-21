Description:
The `SubBytes` kernel is a high-level synthesis design that implements the SubBytes step of the Advanced Encryption Standard (AES) encryption algorithm. The SubBytes step is responsible for substituting the values in the state matrix with values from an S-box. The S-box is a pre-defined table that maps input values to output values using a specific substitution function.

Top-Level Function: `SubBytes`
Complete Function Signature: `void SubBytes(state_t *state);`

Inputs:
- `state`: a 4x4 matrix of 8-bit unsigned integers, representing the state matrix to be encrypted.

Outputs:
- None

Important Data Structures and Data Types:
- `state_t`: a 4x4 matrix of 8-bit unsigned integers, representing the state matrix.
- `uint8_t`: an 8-bit unsigned integer data type.

Sub-Components:
- `getSBoxValue`:
    - Signature: `uint8_t getSBoxValue(uint8_t num);`
    - Details: This function takes an 8-bit unsigned integer as input and returns the corresponding value from the S-box table. The S-box table is a pre-defined table that maps input values to output values using a specific substitution function.