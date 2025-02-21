## kmp_kmp

An implementation of the Knuth-Morris-Pratt (KMP) string searching algorithm, which efficiently searches for a pattern within a given input string. The algorithm preprocesses the pattern to build a lookup table, known as the kmpNext table, which stores the maximum number of characters that can be skipped when a mismatch occurs. This table is then used to search for the pattern in the input string, incrementing a match counter for each occurrence found.

Top-Level Function: `kmp`

Inputs:

- `pattern`: a character array of size `PATTERN_SIZE` (4) representing the pattern to be searched for in the input string.
- `input`: a character array of size `STRING_SIZE` (32411) representing the input string to be searched.
- `kmpNext`: an integer array of size `PATTERN_SIZE` (4) used to store the preprocessed lookup table.
- `n_matches`: an integer array of size 1 used to store the number of matches found.

Outputs:

- `n_matches`: an integer array of size 1 containing the number of matches found.

Important Data Structures and Data Types:

- `kmpNext`: an integer array of size `PATTERN_SIZE` used to store the preprocessed lookup table, where each element represents the maximum number of characters that can be skipped when a mismatch occurs.
- `pattern`: a character array of size `PATTERN_SIZE` representing the pattern to be searched for in the input string.
- `input`: a character array of size `STRING_SIZE` representing the input string to be searched.

Sub-Components:

- `CPF` (Compute Failure Pattern): a sub-component responsible for preprocessing the pattern to build the kmpNext table. It iterates through the pattern, comparing characters and updating the kmpNext table accordingly.
- `kmp` (Knuth-Morris-Pratt): the main sub-component responsible for searching for the pattern in the input string using the preprocessed kmpNext table. It iterates through the input string, comparing characters and incrementing the match counter when a match is found.