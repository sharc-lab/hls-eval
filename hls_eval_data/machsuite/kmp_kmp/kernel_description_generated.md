Kernel Description:
The kmp kernel implements the Knuth-Morris-Pratt (KMP) string searching algorithm, which efficiently searches for a pattern within a given input string. The algorithm preprocesses the pattern to build a lookup table, known as the kmpNext table, which stores the maximum number of characters that can be skipped when a mismatch occurs. This table is then used to search for the pattern in the input string, incrementing a match counter for each occurrence found. The kernel takes four inputs: a character array representing the pattern to be searched for, a character array representing the input string to be searched, an integer array used to store the preprocessed lookup table, and an integer array used to store the number of matches found. The kernel returns the number of matches found.

The algorithm works by first preprocessing the pattern to build the kmpNext table. This is done by iterating through the pattern and comparing characters. The kmpNext table is updated accordingly, with each element representing the maximum number of characters that can be skipped when a mismatch occurs. Once the kmpNext table is built, the kernel searches for the pattern in the input string. This is done by iterating through the input string and comparing characters with the pattern. When a mismatch occurs, the kernel uses the kmpNext table to determine the maximum number of characters that can be skipped, allowing for efficient searching.

The kernel uses the following equation to update the kmpNext table:
$kmpNext[q] = k$, where $k$ is the length of the longest proper prefix of the pattern that is also a suffix. This equation is used to ensure that the kmpNext table is updated correctly, allowing for efficient searching.

The kernel has a time complexity of O(n + m), where n is the length of the input string and m is the length of the pattern. This is because the kernel only needs to iterate through the input string and the pattern once to build the kmpNext table and search for the pattern.

---

Top-Level Function: `kmp`

Complete Function Signature of the Top-Level Function:
`int kmp(char pattern[PATTERN_SIZE], char input[STRING_SIZE], int32_t kmpNext[PATTERN_SIZE], int32_t n_matches[1]);`

Inputs:
- `pattern`: a character array of size `PATTERN_SIZE` (4) representing the pattern to be searched for in the input string. The pattern is a sequence of characters that the kernel will search for in the input string.
- `input`: a character array of size `STRING_SIZE` (32411) representing the input string to be searched. The input string is a sequence of characters that the kernel will search through to find the pattern.
- `kmpNext`: an integer array of size `PATTERN_SIZE` (4) used to store the preprocessed lookup table. The kmpNext table is used to store the maximum number of characters that can be skipped when a mismatch occurs.
- `n_matches`: an integer array of size 1 used to store the number of matches found. The n_matches array is used to store the number of times the pattern is found in the input string.

Outputs:
- `n_matches`: an integer array of size 1 containing the number of matches found. The n_matches array is updated by the kernel to reflect the number of times the pattern is found in the input string.

Important Data Structures and Data Types:
- `kmpNext`: an integer array of size `PATTERN_SIZE` used to store the preprocessed lookup table. The kmpNext table is a critical data structure in the kernel, as it allows for efficient searching by storing the maximum number of characters that can be skipped when a mismatch occurs.
- `pattern`: a character array of size `PATTERN_SIZE` representing the pattern to be searched for in the input string. The pattern is a sequence of characters that the kernel will search for in the input string.
- `input`: a character array of size `STRING_SIZE` representing the input string to be searched. The input string is a sequence of characters that the kernel will search through to find the pattern.

Sub-Components:
- `CPF` (Compute Failure Pattern): a sub-component responsible for preprocessing the pattern to build the kmpNext table. The CPF sub-component iterates through the pattern, comparing characters and updating the kmpNext table accordingly.
    - Signature: `void CPF(char pattern[PATTERN_SIZE], int32_t kmpNext[PATTERN_SIZE]);`
    - Details: The CPF sub-component is a critical part of the kernel, as it allows for efficient searching by building the kmpNext table. The CPF sub-component uses the following equation to update the kmpNext table: $kmpNext[q] = k$, where $k$ is the length of the longest proper prefix of the pattern that is also a suffix.