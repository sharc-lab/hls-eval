Kernel Description:
The `float64_div` kernel function performs 64-bit floating-point division. It takes two 64-bit floating-point numbers as input, `a` and `b`, and returns their quotient. The function first checks for special cases such as division by zero, infinity, and NaN (Not a Number). If the inputs are valid, it extracts the sign, exponent, and significand from both numbers and performs the division. The division is done by estimating the quotient using the `estimateDiv128To64` function, which uses a 128-bit by 64-bit division algorithm. The estimated quotient is then refined by multiplying the divisor by the quotient and subtracting the result from the dividend. The final result is rounded and packed into a 64-bit floating-point number using the `roundAndPackFloat64` function.

The `float64_div` function uses several helper functions, including `extractFloat64Frac`, `extractFloat64Exp`, `extractFloat64Sign`, `packFloat64`, `roundAndPackFloat64`, `normalizeFloat64Subnormal`, `estimateDiv128To64`, `mul64To128`, `add128`, `sub128`, and `shift64RightJamming`. These functions perform tasks such as extracting the significand, exponent, and sign from a 64-bit floating-point number, packing a 64-bit floating-point number, rounding and packing a 64-bit floating-point number, normalizing a subnormal 64-bit floating-point number, estimating the quotient of a 128-bit by 64-bit division, multiplying two 64-bit numbers to produce a 128-bit result, adding and subtracting two 128-bit numbers, and shifting a 64-bit number right with jamming.

The `float64_div` function also uses several variables, including `aSign`, `bSign`, `zSign`, `aExp`, `bExp`, `zExp`, `aSig`, `bSig`, and `zSig`, which store the sign, exponent, and significand of the inputs and output. The function also uses several constants, including `0x7FF`, `0x3FF`, `0x0010000000000000LL`, and `0x0008000000000000LL`, which are used to represent special values such as infinity and NaN.

The `float64_div` function is designed to produce accurate results for a wide range of inputs, including very large and very small numbers. It is also designed to handle special cases such as division by zero and NaN correctly.

---

Top-Level Function: `float64_div`

Complete Function Signature of the Top-Level Function:
`float64 float64_div(float64 a, float64 b);`

Inputs:
- `a`: a 64-bit floating-point number, the dividend.
- `b`: a 64-bit floating-point number, the divisor.

Outputs:
- `return value`: a 64-bit floating-point number, the quotient of `a` and `b`.

Important Data Structures and Data Types:
- `float64`: a 64-bit floating-point number, represented as an unsigned long long integer.
- `bits64`: an unsigned 64-bit integer.
- `sbits64`: a signed 64-bit integer.
- `int8`: an 8-bit signed integer.
- `int16`: a 16-bit signed integer.
- `bits16`: an unsigned 16-bit integer.
- `bits32`: an unsigned 32-bit integer.

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
    - Details: rounds and packs a 64-bit floating-point number from its sign, exponent, and significand.
- `normalizeFloat64Subnormal`:
    - Signature: `void normalizeFloat64Subnormal(bits64 aSig, int16 *zExpPtr, bits64 *zSigPtr);`
    - Details: normalizes a subnormal 64-bit floating-point number.
- `estimateDiv128To64`:
    - Signature: `bits64 estimateDiv128To64(bits64 a0, bits64 a1, bits64 b);`
    - Details: estimates the quotient of a 128-bit by 64-bit division.
- `mul64To128`:
    - Signature: `void mul64To128(bits64 a, bits64 b, bits64 *z0Ptr, bits64 *z1Ptr);`
    - Details: multiplies two 64-bit numbers to produce a 128-bit result.
- `add128`:
    - Signature: `void add128(bits64 a0, bits64 a1, bits64 b0, bits64 b1, bits64 *z0Ptr, bits64 *z1Ptr);`
    - Details: adds two 128-bit numbers.
- `sub128`:
    - Signature: `void sub128(bits64 a0, bits64 a1, bits64 b0, bits64 b1, bits64 *z0Ptr, bits64 *z1Ptr);`
    - Details: subtracts two 128-bit numbers.
- `shift64RightJamming`:
    - Signature: `void shift64RightJamming(bits64 a, int16 count, bits64 *zPtr);`
    - Details: shifts a 64-bit number right with jamming.