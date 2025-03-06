Kernel Description:
The `float64_ge` kernel is designed to perform a greater-than-or-equal-to comparison between two 64-bit floating-point numbers (IEEE 754 double precision). The kernel leverages helper functions to extract the sign, exponent, and fraction parts of the floating-point numbers. It then uses these components to determine the result of the comparison. The design handles special cases such as NaN (Not a Number) values, where the comparison should return false. The kernel is implemented in C++ and uses bitwise operations to efficiently extract and compare the components of the floating-point numbers.

The high-level algorithm involves the following steps:
1. Extract the sign, exponent, and fraction parts of both input floating-point numbers.
2. Check for NaN values in either of the inputs. If a NaN is detected, the function returns false.
3. Compare the signs of the two numbers. If the signs are different, the result is determined based on the sign and the magnitude of the numbers.
4. If the signs are the same, compare the numbers directly. If the numbers are equal, the result is true. Otherwise, the result is determined based on the sign and the magnitude of the numbers.

The kernel is designed to be efficient and handle edge cases such as NaN values and zero values correctly. The use of bitwise operations ensures that the kernel can be synthesized into hardware efficiently.

---

Top-Level Function: `float64_ge`

Complete Function Signature of the Top-Level Function:
`flag float64_ge(float64 a, float64 b);`

Inputs:
- `a`: A 64-bit unsigned integer representing the first floating-point number in IEEE 754 double precision format.
- `b`: A 64-bit unsigned integer representing the second floating-point number in IEEE 754 double precision format.

Outputs:
- `output`: A flag (integer) indicating the result of the comparison. The value is 1 if `a` is greater than or equal to `b`, and 0 otherwise.

Important Data Structures and Data Types:
- `float64`: An unsigned 64-bit integer representing a floating-point number in IEEE 754 double precision format.
- `flag`: An integer used to represent a boolean flag (0 or 1).
- `int16`: A 16-bit signed integer used to represent the exponent part of the floating-point number.
- `bits64`: An unsigned 64-bit integer used to represent the fraction part of the floating-point number.

Sub-Components:
- `extractFloat64Sign`:
    - Signature: `flag extractFloat64Sign(float64 a);`
    - Details: Extracts the sign bit from the 64-bit floating-point number `a`. The sign bit is the most significant bit (bit 63).
- `extractFloat64Exp`:
    - Signature: `int16 extractFloat64Exp(float64 a);`
    - Details: Extracts the exponent part from the 64-bit floating-point number `a`. The exponent is located in bits 52 to 62.
- `extractFloat64Frac`:
    - Signature: `bits64 extractFloat64Frac(float64 a);`
    - Details: Extracts the fraction part from the 64-bit floating-point number `a`. The fraction is located in bits 0 to 51.
- `float64_le`:
    - Signature: `flag float64_le(float64 a, float64 b);`
    - Details: Compares two 64-bit floating-point numbers `a` and `b` to determine if `a` is less than or equal to `b`. This function is used internally by `float64_ge` to perform the comparison.