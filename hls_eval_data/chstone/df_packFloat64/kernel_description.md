Kernel Description:
The `packFloat64` kernel is designed to construct a 64-bit floating-point number (IEEE 754 double precision) from its constituent parts: the sign, exponent, and significand (mantissa). The function takes three inputs: the sign bit, the exponent, and the significand, and combines them into a single 64-bit floating-point number. The sign bit is a single bit (0 for positive, 1 for negative), the exponent is an 11-bit signed integer, and the significand is a 52-bit unsigned integer. The function performs bitwise operations to shift and combine these parts into the correct positions within the 64-bit floating-point format.

---

Top-Level Function: `packFloat64`

Complete Function Signature of the Top-Level Function:
`float64 packFloat64(flag zSign, int16 zExp, bits64 zSig);`

Inputs:
- `zSign`: A single-bit flag representing the sign of the floating-point number. It is of type `flag` (int), where 0 indicates a positive number and 1 indicates a negative number.
- `zExp`: An 11-bit signed integer representing the exponent of the floating-point number. It is of type `int16` (int).
- `zSig`: A 52-bit unsigned integer representing the significand (mantissa) of the floating-point number. It is of type `bits64` (unsigned long long int).

Outputs:
- `output`: A 64-bit floating-point number constructed from the sign, exponent, and significand. It is of type `float64` (unsigned long long int).

Important Data Structures and Data Types:
- `flag`: A single-bit integer used to represent the sign of the floating-point number. It is of type `int`.
- `int16`: A 16-bit signed integer used to represent the exponent of the floating-point number. It is of type `int`.
- `bits64`: A 64-bit unsigned integer used to represent the significand and the final floating-point number. It is of type `unsigned long long int`.
- `float64`: A 64-bit unsigned integer used to represent the final floating-point number. It is of type `unsigned long long int`.

Sub-Components:
- None