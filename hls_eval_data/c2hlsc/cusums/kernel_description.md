Kernel Description:
The CumulativeSums kernel is a high-level synthesis design that calculates the cumulative sum of a binary array `epsilon` and returns the indices of the maximum and minimum cumulative sums. The kernel is designed to operate on a large array of 0s and 1s, where each element represents a binary value. The cumulative sum is calculated by iterating through the array and incrementing or decrementing a running sum based on the binary value. The maximum and minimum cumulative sums are tracked and returned as output.

Top-Level Function: `CumulativeSums`
Complete Function Signature of the Top-Level Function: `void CumulativeSums(int *res_sup, int *res_inf);`

Inputs:
- `epsilon`: a binary array of size `N` (20000 in this implementation), where each element is either 0 or 1.

Outputs:
- `res_sup`: the index of the maximum cumulative sum
- `res_inf`: the index of the minimum cumulative sum

Important Data Structures and Data Types:
- `int`: a 32-bit signed integer type used for indexing and storing cumulative sums
- `epsilon`: a binary array of size `N` (20000 in this implementation), where each element is either 0 or 1

Sub-Components:
- `CumulativeSums`:
    - Signature: `void CumulativeSums(int *res_sup, int *res_inf);`
    - Details: The kernel iterates through the `epsilon` array, calculating the cumulative sum and tracking the maximum and minimum cumulative sums. The cumulative sum is initialized to 0, and the maximum and minimum cumulative sums are initialized to 0 and `N-1` respectively. For each element in the array, the cumulative sum is incremented or decremented based on the binary value, and the maximum and minimum cumulative sums are updated accordingly. Finally, the indices of the maximum and minimum cumulative sums are returned as output.