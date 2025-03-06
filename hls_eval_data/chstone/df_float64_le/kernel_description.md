Kernel Description:
The `float64_le` kernel is designed to perform a less-than-or-equal comparison between two 64-bit floating-point numbers (IEEE 754 double precision). The kernel extracts the sign, exponent, and fraction parts of each floating-point number and uses these components to determine the result of the comparison. The design handles special cases such as NaN (Not a Number) values, where the comparison should return false. The kernel is implemented in C++ and uses bitwise operations to efficiently extract and compare the components of the floating-point numbers.

The algorithm involves the following steps:
1. Extract the sign bit of each floating-point number.
2. Extract the exponent bits of each floating-point number.
3. Extract the fraction bits of each floating-point number.
4. Check for NaN values by verifying if the exponent is all ones and the fraction is non-zero.
5. If the signs of the two numbers are different, the result is determined based on the sign bits.
6. If the signs are the same, the result is determined by comparing the numbers directly.

---

Top-Level Function: `float64_le`

Complete Function Signature of the Top-Level Function:
`flag float64_le(float64 a, float64 b);`

Inputs:
- `a`: A 64-bit unsigned integer representing the first floating-point number in IEEE 754 double precision format.
- `b`: A 64-bit unsigned integer representing the second floating-point number in IEEE 754 double precision format.

Outputs:
- `output`: A flag (integer) indicating the result of the comparison. The value is 1 if `a` is less than or equal to `b`, and 0 otherwise.

Important Data Structures and Data Types:
- `flag`: An integer type used to represent boolean values (0 or 1).
- `int16`: A 16-bit signed integer type used to represent the exponent part of the floating-point number.
- `bits64`: A 64-bit unsigned integer type used to represent the fraction part of the floating-point number.
- `float64`: A 64-bit unsigned integer type used to represent the entire floating-point number.

Sub-Components:
- `extractFloat64Sign`:
    - Signature: `flag extractFloat64Sign(float64 a);`
    - Details: Extracts the sign bit from the 64-bit floating-point number `a` by right-shifting the number by 63 bits.
- `extractFloat64Exp`:
    - Signature: `int16 extractFloat64Exp(float64 a);`
    - Details: Extracts the exponent bits from the 64-bit floating-point number `a` by right-shifting the number by 52 bits and masking the lower 11 bits.
- `extractFloat64Frac`:
    - Signature: `bits64 extractFloat64Frac(float64 a);`
    - Details: Extracts the fraction bits from the 64-bit floating-point number `a` by masking the lower 52 bits.