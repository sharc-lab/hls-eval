Kernel Description:
The `extractFloat64Frac` kernel is designed to extract the fractional part of a 64-bit floating-point number (IEEE 754 double precision format). The kernel performs a bitwise AND operation between the input floating-point number and a mask to isolate the fractional part of the number. The IEEE 754 double precision format consists of 1 bit for the sign, 11 bits for the exponent, and 52 bits for the fractional part. By applying the mask, the sign and exponent bits are cleared, leaving only the fractional part.

The kernel is implemented in C++ and utilizes two custom data types: `bits64` and `float64`, both defined as `unsigned long long int`. The input to the kernel is a 64-bit floating-point number, and the output is a 64-bit unsigned integer representing the fractional part of the input number. The kernel is straightforward and efficient, leveraging bitwise operations to achieve the desired result.

---

Top-Level Function: `extractFloat64Frac`

Complete Function Signature of the Top-Level Function:
`bits64 extractFloat64Frac(float64 a);`

Inputs:
- `a`: A 64-bit unsigned integer representing a floating-point number in IEEE 754 double precision format. The input is expected to be in the form of an `unsigned long long int` to facilitate bitwise operations.

Outputs:
- The function returns a 64-bit unsigned integer (`bits64`) that contains the fractional part of the input floating-point number. The returned value is obtained by masking out the sign and exponent bits, leaving only the 52-bit fractional part.

Important Data Structures and Data Types:
- `bits64`: An unsigned 64-bit integer type (`unsigned long long int`) used to represent the fractional part of the floating-point number.
- `float64`: An unsigned 64-bit integer type (`unsigned long long int`) used to represent the input floating-point number in IEEE 754 double precision format.

Sub-Components:
- None