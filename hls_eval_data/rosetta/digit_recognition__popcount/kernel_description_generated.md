Kernel Description:
The popcount kernel is designed to count the number of 1's in a given 256-bit binary number. This is achieved through a simple iterative approach, where each bit of the input number is checked and the count is incremented accordingly. The kernel utilizes a for loop to iterate over each bit of the 256-bit number, adding the value of the current bit to a running total. This process can be represented by the equation: $cnt = \sum_{i=0}^{255} x_i$, where $x_i$ is the i-th bit of the input number and $cnt$ is the final count of 1's. The kernel's functionality is based on the principle of bit manipulation, where the value of each bit is either 0 or 1, and the count is incremented by the value of the current bit.

---

Top-Level Function: `popcount`

Complete Function Signature of the Top-Level Function:
`int popcount(WholeDigitType x);`

Inputs:
- `x`: a 256-bit binary number of type `WholeDigitType`, which is an unsigned integer type with 256 bits. The input number is represented as an array of 256 bits, where each bit can have a value of either 0 or 1.

Outputs:
- `return value`: an integer representing the count of 1's in the input number.

Important Data Structures and Data Types:
- `WholeDigitType`: a 256-bit unsigned integer type, represented as an array of 256 bits. This data type is used to represent the input number and is defined in the `popcount.h` header file.

Sub-Components:
- None