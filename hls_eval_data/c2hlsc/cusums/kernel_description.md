Kernel Description:
The CumulativeSums kernel is designed to calculate the maximum and minimum cumulative sums of a given array of binary values, represented by the epsilon array. The cumulative sum is calculated by iterating through the epsilon array and incrementing or decrementing a running sum S based on the value of the current element. If the current element is 1 (true), the sum S is incremented; otherwise, it is decremented. The maximum and minimum cumulative sums are updated accordingly during the iteration. The kernel uses a simple iterative approach to calculate the cumulative sums, avoiding unnecessary complexity. The algorithm can be represented by the following equations:
- $S_{k+1} = S_k + 1$ if $\epsilon_k = 1$
- $S_{k+1} = S_k - 1$ if $\epsilon_k = 0$
- $sup_{k+1} = max(sup_k, S_{k+1})$
- $inf_{k+1} = min(inf_k, S_{k+1})$
where $S_k$ is the cumulative sum at the k-th iteration, $sup_k$ is the maximum cumulative sum up to the k-th iteration, and $inf_k$ is the minimum cumulative sum up to the k-th iteration.

The kernel has a time complexity of O(N), where N is the size of the epsilon array, and a space complexity of O(1), excluding the input and output arrays. The kernel assumes that the epsilon array is initialized before calling the CumulativeSums function.

---

Top-Level Function: `CumulativeSums`

Complete Function Signature of the Top-Level Function:
`void CumulativeSums(int *res_sup, int *res_inf);`

Inputs:
- `res_sup`: a pointer to an integer that will store the maximum cumulative sum
- `res_inf`: a pointer to an integer that will store the minimum cumulative sum

Outputs:
- `res_sup`: the maximum cumulative sum
- `res_inf`: the minimum cumulative sum

Important Data Structures and Data Types:
- `epsilon`: an array of integers representing the binary values used to calculate the cumulative sums. The array has a fixed size of N, where N is defined as 20000.

Sub-Components:
- None