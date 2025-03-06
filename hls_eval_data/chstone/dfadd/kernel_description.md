Kernel Description:
The float64_add kernel is a high-level synthesis design that implements the addition of two 64-bit floating-point numbers. The design takes two input floating-point numbers, a and b, and produces their sum as output. The kernel handles various cases, including the addition of positive and negative numbers, as well as the handling of special values such as NaN (Not a Number) and infinity.

The design uses a combination of bitwise operations and arithmetic operations to perform the addition. The input floating-point numbers are first unpacked into their sign, exponent, and significand components. The significands are then added or subtracted based on the signs of the input numbers, and the result is packed back into a floating-point number.

The kernel also handles rounding and exception handling. The rounding mode is determined by the float_rounding_mode variable, which can be set to one of four values: 0 (round to nearest even), 1 (round to positive infinity), 2 (round to negative infinity), or 3 (round to zero). The kernel also sets exception flags if the result is NaN, infinity, or if the result overflows or underflows.

The design uses several sub-components, including the addFloat64Sigs and subFloat64Sigs functions, which perform the actual addition and subtraction of the significands. The normalizeRoundAndPackFloat64 function is used to normalize the result and pack it back into a floating-point number.

The kernel uses several data structures, including the float64 data type, which represents a 64-bit floating-point number. The design also uses several constants, including the float_rounding_mode variable and the exception flags.

The algorithm used by the kernel can be summarized as follows:

1. Unpack the input floating-point numbers into their sign, exponent, and significand components.
2. Determine the signs of the input numbers and perform the addition or subtraction accordingly.
3. Pack the result back into a floating-point number.
4. Handle rounding and exception handling based on the float_rounding_mode variable and the result.

The kernel can be represented mathematically using the following equation:

$$z = a + b$$

where $z$ is the result, $a$ and $b$ are the input floating-point numbers, and $+$ represents the addition operation.

---

Top-Level Function: `float64_add`

Complete Function Signature of the Top-Level Function:
`float64 float64_add(float64 a, float64 b);`

Inputs:
- `a`: a 64-bit floating-point number, represented as an unsigned long long integer.
- `b`: a 64-bit floating-point number, represented as an unsigned long long integer.

Outputs:
- `result`: the sum of `a` and `b`, represented as a 64-bit floating-point number.

Important Data Structures and Data Types:
- `float64`: a 64-bit floating-point number, represented as an unsigned long long integer.
- `int8`: an 8-bit integer, used to represent the float_rounding_mode variable and exception flags.
- `int16`: a 16-bit integer, used to represent the exponent component of a floating-point number.
- `bits64`: an unsigned 64-bit integer, used to represent the significand component of a floating-point number.

Sub-Components:
- `addFloat64Sigs`:
    - Signature: `float64 addFloat64Sigs(float64 a, float64 b, flag zSign);`
    - Details: performs the addition of two significands, based on the signs of the input numbers.
- `subFloat64Sigs`:
    - Signature: `float64 subFloat64Sigs(float64 a, float64 b, flag zSign);`
    - Details: performs the subtraction of two significands, based on the signs of the input numbers.
- `normalizeRoundAndPackFloat64`:
    - Signature: `float64 normalizeRoundAndPackFloat64(flag zSign, int16 zExp, bits64 zSig);`
    - Details: normalizes the result and packs it back into a floating-point number, handling rounding and exception handling.