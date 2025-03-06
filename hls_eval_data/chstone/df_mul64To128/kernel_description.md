Kernel Description:
The `mul64To128` kernel is designed to perform a 64-bit by 64-bit multiplication and produce a 128-bit result. The multiplication is broken down into smaller parts to handle the large product size, which is typical in hardware design to manage bit-width limitations and improve efficiency. The algorithm splits each 64-bit input into two 32-bit parts, performs partial multiplications, and then combines these results to form the final 128-bit product. This approach ensures that each multiplication step remains within the 64-bit range, avoiding overflow issues. The kernel handles the carry propagation between the partial products to ensure the correctness of the final result.

The multiplication process can be described mathematically as follows:
Let \( a = a_{high} \cdot 2^{32} + a_{low} \) and \( b = b_{high} \cdot 2^{32} + b_{low} \), where \( a_{high}, a_{low}, b_{high}, b_{low} \) are 32-bit values.
The product \( z = a \cdot b \) can be expanded as:
\[ z = (a_{high} \cdot 2^{32} + a_{low}) \cdot (b_{high} \cdot 2^{32} + b_{low}) \]
\[ z = a_{high} \cdot b_{high} \cdot 2^{64} + (a_{high} \cdot b_{low} + a_{low} \cdot b_{high}) \cdot 2^{32} + a_{low} \cdot b_{low} \]
The terms \( a_{high} \cdot b_{high} \), \( a_{high} \cdot b_{low} \), and \( a_{low} \cdot b_{high} \) are computed separately, and their contributions are combined to form the final 128-bit result. The kernel carefully manages the carry from the middle terms to the higher-order terms to ensure the result is accurate.

---

Top-Level Function: `mul64To128`

Complete Function Signature of the Top-Level Function:
`void mul64To128(bits64 a, bits64 b, bits64 *z0Ptr, bits64 *z1Ptr);`

Inputs:
- `a`: A 64-bit unsigned integer representing the first multiplicand.
- `b`: A 64-bit unsigned integer representing the second multiplicand.

Outputs:
- `z0Ptr`: A pointer to a 64-bit unsigned integer where the lower 64 bits of the product will be stored.
- `z1Ptr`: A pointer to a 64-bit unsigned integer where the upper 64 bits of the product will be stored.

Important Data Structures and Data Types:
- `bits64`: An unsigned 64-bit integer type used for the inputs and outputs of the multiplication.
- `bits32`: An unsigned 32-bit integer type used for intermediate calculations to split the 64-bit inputs into manageable parts.

Sub-Components:
- None