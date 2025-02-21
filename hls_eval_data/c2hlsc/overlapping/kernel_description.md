Description:
The Overlapping kernel is a high-level synthesis design that computes the chi-squared statistic for a given sequence of binary values. The kernel takes as input a sequence of binary values, represented as an array of 0s and 1s, and outputs a single value representing the chi-squared statistic. The kernel uses a sliding window approach to compute the chi-squared statistic, where each window is 9 elements long. The kernel iterates over the input sequence, counting the number of matches between the current window and the input sequence. The kernel then computes the chi-squared statistic by summing the squared counts of each match.

Top-Level Function: `Overlapping`
Complete Function Signature of the Top-Level Function: `void Overlapping(double *result);`

Inputs:
- `epsilon`: an array of 0s and 1s, representing the input sequence, with a size of `N` (defined in `overlapping.h`).

Outputs:
- `result`: a single double-precision floating-point value representing the chi-squared statistic.

Important Data Structures and Data Types:
- `double`: a double-precision floating-point data type used to represent the chi-squared statistic.
- `int`: an integer data type used to represent indices and counts.
- `char`: a character data type used to represent the binary values in the input sequence.
- `unsigned int`: an unsigned integer data type used to represent the counts of matches.

Sub-Components:
- `Overlapping`:
    - Signature: `void Overlapping(double *result);`
    - Details: The kernel iterates over the input sequence, counting the number of matches between the current window and the input sequence. The kernel then computes the chi-squared statistic by summing the squared counts of each match.
    - Implementation Quirks: The kernel uses a sliding window approach, where each window is 9 elements long. The kernel also uses a lookup table to store the probabilities of each match.
    - Edge Cases: The kernel assumes that the input sequence is a valid array of 0s and 1s. If the input sequence is invalid, the kernel may produce incorrect results.
    - Design Decisions: The kernel uses a double-precision floating-point data type to represent the chi-squared statistic to ensure accurate results. The kernel also uses a lookup table to store the probabilities of each match to reduce the computational complexity of the algorithm.