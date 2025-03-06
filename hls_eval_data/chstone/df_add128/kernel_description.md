Kernel Description:
The `add128` kernel is designed to perform a 128-bit addition operation on two input numbers, each represented as a pair of 64-bit unsigned integers. The kernel takes six inputs: `a0` and `a1` representing the two 64-bit parts of the first input number, `b0` and `b1` representing the two 64-bit parts of the second input number, and `z0Ptr` and `z1Ptr` which are pointers to store the two 64-bit parts of the result. The kernel first calculates the sum of the high 64 bits of the two input numbers (`a1` and `b1`) and stores the result in `z1`. Then, it calculates the sum of the low 64 bits of the two input numbers (`a0` and `b0`) and adds the carry from the previous addition (which is determined by checking if `z1` is less than `a1`) to produce the final result, which is stored in `z0`. This operation can be represented by the following equation:
$z_1 = a_1 + b_1$
$z_0 = a_0 + b_0 + \text{carry}$, where $\text{carry} = (z_1 < a_1)$.

---

Top-Level Function: `add128`

Complete Function Signature of the Top-Level Function:
`void add128(bits64 a0, bits64 a1, bits64 b0, bits64 b1, bits64 *z0Ptr, bits64 *z1Ptr);`

Inputs:
- `a0`: the low 64 bits of the first input number, represented as an unsigned 64-bit integer.
- `a1`: the high 64 bits of the first input number, represented as an unsigned 64-bit integer.
- `b0`: the low 64 bits of the second input number, represented as an unsigned 64-bit integer.
- `b1`: the high 64 bits of the second input number, represented as an unsigned 64-bit integer.
- `z0Ptr`: a pointer to store the low 64 bits of the result, represented as an unsigned 64-bit integer.
- `z1Ptr`: a pointer to store the high 64 bits of the result, represented as an unsigned 64-bit integer.

Outputs:
- `*z0Ptr`: the low 64 bits of the result, stored in the memory location pointed to by `z0Ptr`.
- `*z1Ptr`: the high 64 bits of the result, stored in the memory location pointed to by `z1Ptr`.

Important Data Structures and Data Types:
- `bits64`: an unsigned 64-bit integer type, used to represent the input numbers and the result.

Sub-Components:
- None