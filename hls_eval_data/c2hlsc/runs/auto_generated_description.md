Description:
The `Runs` kernel is a high-level synthesis design that counts the number of ones in an array `epsilon` and the number of changes from 0 to 1 and 1 to 0 in the array. The kernel takes two integer pointers as inputs, `res_S` and `res_V`, which are used to return the results of the counting operations. The kernel iterates through the `epsilon` array, incrementing a counter `S` for each one encountered and a counter `V` for each change in the array. The final values of `S` and `V` are returned through the `res_S` and `res_V` pointers, respectively.

Top-Level Function: `Runs`
Complete Function Signature: `void Runs(int *res_S, int *res_V);`

Inputs:
- `res_S`: a pointer to an integer, used to return the count of ones in the `epsilon` array
- `res_V`: a pointer to an integer, used to return the count of changes in the `epsilon` array

Outputs:
- `S`: the count of ones in the `epsilon` array
- `V`: the count of changes in the `epsilon` array

Important Data Structures and Data Types:
- `int`: a 32-bit signed integer type used to represent the counters `S` and `V`
- `epsilon`: an array of 0s and 1s, used as input to the kernel

Sub-Components:
- None: the `Runs` kernel is a single, self-contained function that performs the counting operations.