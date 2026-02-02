Kernel Description:
The `ms_mergesort` kernel implements the merge sort algorithm, a divide-and-conquer approach to sorting an array of elements. The design takes an array of integers as input and produces a sorted array as output. The algorithm works by recursively dividing the input array into smaller subarrays, sorting each subarray, and then merging the sorted subarrays to produce the final sorted array. The merge sort algorithm has a time complexity of $O(n \log n)$, where $n$ is the number of elements in the input array. The kernel uses a temporary array to store intermediate results during the merge process.

The `ms_mergesort` kernel iterates over the input array, recursively dividing it into smaller subarrays, and calling the `merge` sub-component to sort and merge each subarray. The `merge` sub-component takes three indices (`start`, `m`, and `stop`) and the input array `a` as inputs, and produces a merged and sorted subarray as output. The `merge` sub-component consists of three loops: `merge_label1` and `merge_label2` copy the left and right halves of the input array into a temporary array, respectively, and `merge_label3` merges the two halves into a single sorted array.

The kernel uses a constant integer value `SIZE` to represent the size of the input array, and an integer data type `TYPE` (int32_t) to represent the elements of the input array. The kernel also uses a temporary array `temp` of `SIZE` elements of type `TYPE` to store intermediate results during the merge process.

---

Top-Level Function: `ms_mergesort`

Complete Function Signature of the Top-Level Function:
`void ms_mergesort(TYPE a[SIZE]);`

Inputs:
- `a`: an array of `SIZE` elements of type `TYPE` (int32_t), representing the input array to be sorted.

Outputs:
- `a`: the sorted array of `SIZE` elements of type `TYPE` (int32_t), representing the output of the merge sort algorithm.

Important Data Structures and Data Types:
- `TYPE`: an integer data type (int32_t) used to represent the elements of the input array.
- `SIZE`: a constant integer value (2048) representing the size of the input array.
- `temp`: a temporary array of `SIZE` elements of type `TYPE` used to store intermediate results during the merge process.

Sub-Components:
- `merge`:
    - Signature: `void merge(TYPE a[SIZE], int start, int m, int stop);`
    - Details: The `merge` sub-component implements the merge step of the merge sort algorithm, taking three indices (`start`, `m`, and `stop`) and the input array `a` as inputs, and producing a merged and sorted subarray as output. The `merge` sub-component consists of three loops: `merge_label1` and `merge_label2` copy the left and right halves of the input array into a temporary array, respectively, and `merge_label3` merges the two halves into a single sorted array.