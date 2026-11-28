Kernel Description:
The `Overlapping` kernel is designed to perform a statistical analysis on a sequence of binary data. The primary functionality involves counting the occurrences of a specific pattern within a sliding window across a large dataset and then computing a chi-square statistic based on these counts. The pattern to be matched is a sequence of nine consecutive ones (`1, 1, 1, 1, 1, 1, 1, 1, 1`). The dataset is a one-dimensional array of integers, where each integer is either 0 or 1. The kernel iterates over the dataset in a sliding window fashion, checking for matches of the pattern and updating a count array (`nu`) based on the number of matches found in each window. The chi-square statistic is then computed using predefined weights (`pi`) and the counts in `nu`.

---

Top-Level Function: `Overlapping`

Complete Function Signature of the Top-Level Function:
`void Overlapping(double *result, int epsilon[N]);`

Inputs:
- `result`: A pointer to a double where the computed chi-square statistic will be stored. The data type is `double` to accommodate the potential range of the chi-square value.
- `epsilon`: An array of integers of size `N` (1056768) representing the binary dataset. Each element in the array is either 0 or 1.

Outputs:
- `result`: The computed chi-square statistic is stored in the location pointed to by `result`.

Important Data Structures and Data Types:
- `nu`: An array of unsigned integers of size 6 used to count the number of windows with 0 to 4 matches and a combined count for 5 or more matches. The data type is `unsigned int` and the size is 6.
- `pi`: An array of doubles of size 6 containing predefined weights used in the chi-square computation. The data type is `double` and the size is 6.
- `sequence`: An array of characters of size 9 representing the pattern to be matched. The data type is `char` and the size is 9.

Sub-Components:
- None
Complete computation and constants:
- Partition epsilon into1024 contiguous blocks of1032 bits. In each block, examine1024 starting offsets j=0..1023; a match means epsilon[i*1032+j+k]==1 for every k=0..8. Overlapping matches are counted.
- Initialize nu[0..5] to zero. For a block with W matches, increment nu[W] if W<=4, otherwise nu[5].
- The six predefined weights, in order, are double literals {2.746566,5.386218,7.17457,9.94322,14.198031,7.1497515}.
- Set result to sum over k=0..5 of double(nu[k])*double(nu[k])*pi[k], in increasing k. This weighted statistic is the intended quantity in this task; do not substitute another probability normalization or NIST formulation.
- All input elements are binary. Input is read-only in behavior; only *result is a defined output.
