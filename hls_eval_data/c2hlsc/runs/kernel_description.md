Description:
The `Runs` kernel is a high-level synthesis design that counts the number of ones in an array `epsilon` and the number of changes from 0 to 1 and 1 to 0 in the array. The design is implemented as a C++ function that takes two integer pointers as inputs, `res_S` and `res_V`, and returns the counts through these pointers.

Top-Level Function: `Runs`
Complete Function Signature: `void Runs(int *res_S, int *res_V);`

Inputs:
- `res_S`: a pointer to an integer that will hold the count of ones in the array `epsilon`.
- `res_V`: a pointer to an integer that will hold the count of changes from 0 to 1 and 1 to 0 in the array `epsilon`.

Outputs:
- `res_S`: the count of ones in the array `epsilon`.
- `res_V`: the count of changes from 0 to 1 and 1 to 0 in the array `epsilon`.

Important Data Structures and Data Types:
- `int`: a 32-bit signed integer type used to represent the counts and array indices.
- `epsilon`: an array of 0s and 1s of size 65535, used as input to the `Runs` kernel.

Sub-Components:
- `Runs`:
    - Signature: `void Runs(int *res_S, int *res_V);`
    - Details: The `Runs` kernel function iterates over the array `epsilon` and counts the number of ones using a simple loop. It then iterates over the array again to count the number of changes from 0 to 1 and 1 to 0. The counts are stored in the `res_S` and `res_V` pointers, respectively.