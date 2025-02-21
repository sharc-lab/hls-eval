Description:
The CumulativeSums kernel is a high-level synthesis design that calculates the cumulative sum of a binary array `epsilon` and returns the indices of the maximum and minimum cumulative sums. The kernel iterates through the array, incrementing or decrementing a running sum `S` based on the value of each element in the array. The maximum and minimum cumulative sums are tracked using variables `sup` and `inf`, respectively. The kernel returns the indices of these maximum and minimum cumulative sums as output.

Top-Level Function: `CumulativeSums`
Complete Function Signature: `void CumulativeSums(int *res_sup, int *res_inf);`

Inputs:
- `res_sup`: a pointer to an integer variable that will hold the index of the maximum cumulative sum
- `res_inf`: a pointer to an integer variable that will hold the index of the minimum cumulative sum

Outputs:
- `res_sup`: the index of the maximum cumulative sum
- `res_inf`: the index of the minimum cumulative sum

Important Data Structures and Data Types:
- `int`: a 32-bit signed integer type used to represent the indices and cumulative sums
- `epsilon`: a 32-bit signed integer array of size `N` (20000) containing binary values (0s and 1s)

Sub-Components:
- None: the CumulativeSums kernel is a standalone function with no sub-components