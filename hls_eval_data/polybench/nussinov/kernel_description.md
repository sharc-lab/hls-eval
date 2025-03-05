Kernel Description:
The Nussinov kernel is an algorithm for predicting RNA folding, which is an instance of dynamic programming. It takes an RNA sequence as input and produces a dynamic programming table as output. The table is filled using a recursive formula that considers the maximum score of four possible cases: (1) the maximum score of the sub-problem without considering the current base pair, (2) the maximum score of the sub-problem without considering the current base, (3) the maximum score of the sub-problem with considering the current base pair, and (4) the maximum score of the sub-problem with considering the current base pair and the maximum score of the sub-problem without considering the current base pair.

It takes the following as input,

- `seq`: RNA sequence of length $N$. The valid entries are one of 'A' 'G' 'C' 'T'. (or 'U' in place of 'T').

and gives the following as output:

- `table`: $N \times N$ triangular matrix, which is the dynamic programming table.

The table is filled using the following formula:

$$
table(i,j) = \max
\begin{cases}
table(i+1,j) \\
table(i,j-1) \\
table(i+1,j-1) + w(i,j) \\
\max_{i < k < j}(table(i,k) + table(k+1,j))
\end{cases}
$$

where $w$ is the scoring function that evaluate the pair of sequences $seq[i]$ and $seq[j]$. For Nussinov algorithm, the scoring function returns 1 if the sequences are complementary (either 'A' with 'T' or 'G' with 'C'), and 0 otherwise.

---

Top-Level Function: `kernel_nussinov`

Complete Function Signature of the Top-Level Function:
`void kernel_nussinov(char seq[60], int table[60][60]);`

Inputs:
- `seq`: an RNA sequence of length 60, where each element is one of 'A', 'G', 'C', 'T', or 'U'. The sequence is stored in a 1D array of characters.

Outputs:
- `table`: a 2D array of integers, representing the dynamic programming table. The table is a triangular matrix of size 60x60, where each element `table[i][j]` represents the maximum score of the sub-problem considering the RNA sequence from `i` to `j`.

Important Data Structures and Data Types:
- `seq`: a 1D array of characters, representing the RNA sequence.
- `table`: a 2D array of integers, representing the dynamic programming table.

Sub-Components:
- None