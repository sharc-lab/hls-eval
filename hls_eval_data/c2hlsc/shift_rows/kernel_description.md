Description:
The ShiftRows kernel is a high-level synthesis hardware design that implements the ShiftRows operation from the Advanced Encryption Standard (AES) algorithm. The ShiftRows operation is a key component of the AES encryption and decryption process, responsible for rearranging the columns of the state matrix to prepare it for the next round of encryption or decryption.

Top-Level Function: `ShiftRows`
Complete Function Signature of the Top-Level Function: `void ShiftRows(state_t *state);`

Inputs:
- `state`: a 4x4 matrix of 8-bit unsigned integers, representing the current state of the AES encryption or decryption process.

Outputs:
- None

Important Data Structures and Data Types:
- `state_t`: a 4x4 matrix of 8-bit unsigned integers, representing the current state of the AES encryption or decryption process.

Sub-Components:
- `ShiftRows`:
    - Signature: `void ShiftRows(state_t *state);`
    - Details: The ShiftRows function takes a 4x4 state matrix as input and rearranges its columns according to the ShiftRows operation. The function consists of three main parts: rotating the first row, rotating the second row, and rotating the third row. Each row is rotated by a different offset, with the first row not being rotated at all. The function uses temporary variables to store the values being shifted and updates the state matrix accordingly.