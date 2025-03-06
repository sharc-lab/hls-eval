Kernel Description:
The `float64_mul` kernel function is designed to perform multiplication of two 64-bit floating-point numbers. The function takes two input floating-point numbers, `a` and `b`, and returns their product. The kernel function handles various cases, including multiplication of normal numbers, subnormal numbers, and special values such as NaN (Not a Number) and infinity.

The function first extracts the sign, exponent, and significand from the input floating-point numbers. It then checks for special cases, such as NaN and infinity, and handles them accordingly. If both inputs are normal numbers, the function performs the multiplication and rounds the result to the nearest representable floating-point number.

The multiplication is performed using a 64-bit by 64-bit multiplication algorithm, which produces a 128-bit product. The product is then rounded and packed into a 64-bit floating-point number.

The kernel function also handles subnormal numbers, which are numbers that are too small to be represented in the normal floating-point format. In this case, the function normalizes the subnormal numbers and then performs the multiplication.

The function uses several helper functions, including `extractFloat64Frac`, `extractFloat64Exp`, `extractFloat64Sign`, `packFloat64`, `roundAndPackFloat64`, `normalizeFloat64Subnormal`, `mul64To128`, and `shift64RightJamming`. These functions perform tasks such as extracting the significand, exponent, and sign from a floating-point number, packing a floating-point number, rounding a floating-point number, and performing 64-bit by 64-bit multiplication.

The kernel function is designed to be highly accurate and to handle all possible input cases. It is also designed to be efficient and to minimize the number of operations required to perform the multiplication.

The algorithm used in the kernel function can be represented by the following equation:

$$z = \text{round}(a \times b)$$

where $z$ is the result of the multiplication, $a$ and $b$ are the input floating-point numbers, and $\text{round}$ is the rounding function.

The rounding function used in the kernel function is based on the IEEE 754 floating-point standard, which specifies four rounding modes: round to nearest, round to positive infinity, round to negative infinity, and round to zero. The kernel function uses the round to nearest mode by default, but can be configured to use other rounding modes.

---

Top-Level Function: `float64_mul`

Complete Function Signature of the Top-Level Function:
`float64 float64_mul(float64 a, float64 b);`

Inputs:
- `a`: a 64-bit floating-point number, represented as an unsigned 64-bit integer.
- `b`: a 64-bit floating-point number, represented as an unsigned 64-bit integer.

Outputs:
- `return value`: the product of `a` and `b`, represented as a 64-bit floating-point number.

Important Data Structures and Data Types:
- `float64`: a 64-bit floating-point number, represented as an unsigned 64-bit integer.
- `bits64`: an unsigned 64-bit integer.
- `int16`: a signed 16-bit integer.
- `int8`: a signed 8-bit integer.
- `flag`: a boolean value, represented as a signed integer.

Sub-Components:
- `extractFloat64Frac`:
    - Signature: `bits64 extractFloat64Frac(float64 a);`
    - Details: extracts the significand from a 64-bit floating-point number.
- `extractFloat64Exp`:
    - Signature: `int16 extractFloat64Exp(float64 a);`
    - Details: extracts the exponent from a 64-bit floating-point number.
- `extractFloat64Sign`:
    - Signature: `flag extractFloat64Sign(float64 a);`
    - Details: extracts the sign from a 64-bit floating-point number.
- `packFloat64`:
    - Signature: `float64 packFloat64(flag zSign, int16 zExp, bits64 zSig);`
    - Details: packs a 64-bit floating-point number from its sign, exponent, and significand.
- `roundAndPackFloat64`:
    - Signature: `float64 roundAndPackFloat64(flag zSign, int16 zExp, bits64 zSig);`
    - Details: rounds a 64-bit floating-point number and packs it into a 64-bit floating-point number.
- `normalizeFloat64Subnormal`:
    - Signature: `void normalizeFloat64Subnormal(bits64 aSig, int16 *zExpPtr, bits64 *zSigPtr);`
    - Details: normalizes a subnormal 64-bit floating-point number.
- `mul64To128`:
    - Signature: `void mul64To128(bits64 a, bits64 b, bits64 *z0Ptr, bits64 *z1Ptr);`
    - Details: performs 64-bit by 64-bit multiplication and produces a 128-bit product.
- `shift64RightJamming`:
    - Signature: `void shift64RightJamming(bits64 a, int16 count, bits64 *zPtr);`
    - Details: shifts a 64-bit integer to the right and jams the result into a 64-bit integer.