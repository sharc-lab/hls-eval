Description:
The `Overlapping` kernel is a high-level synthesis design that computes the chi-squared statistic for a given sequence of binary values. The kernel takes as input a sequence of binary values represented as a 1D array `epsilon` of size `N`, where `N` is a large integer. The kernel iterates over the sequence and counts the number of overlapping matches between the sequence and a fixed pattern `sequence` of length 9. The counts are stored in an array `nu` of size 6. The kernel then computes the chi-squared statistic by summing the squared counts multiplied by corresponding probabilities `pi`. The result is stored in a single output variable `result`.

Top-Level Function: `Overlapping`
Complete Function Signature: `void Overlapping(double *result);`

Inputs:
- `epsilon`: a 1D array of size `N` representing the sequence of binary values, where `N` is a large integer. The data type is `int` and the layout is row-major.

Outputs:
- `result`: a single output variable representing the computed chi-squared statistic. The data type is `double` and the layout is not specified.

Important Data Structures and Data Types:
- `nu`: an array of size 6 representing the counts of overlapping matches. The data type is `unsigned int` and the layout is row-major.
- `pi`: an array of size 6 representing the probabilities corresponding to the counts. The data type is `double` and the layout is row-major.
- `sequence`: a fixed pattern of length 9 representing the sequence to be matched. The data type is `char` and the layout is not specified.

Sub-Components:
- The kernel consists of a single loop that iterates over the sequence `epsilon`. The loop has three nested loops that iterate over the sequence, the pattern `sequence`, and the counts `nu`. The kernel also includes a single computation of the chi-squared statistic using the counts and probabilities.