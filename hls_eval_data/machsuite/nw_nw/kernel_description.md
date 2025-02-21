## nw_nw

An implementation of the Needleman-Wunsch algorithm for global pairwise sequence alignment. The algorithm is a dynamic programming approach that finds the optimal alignment between two input sequences, SEQA and SEQB, by maximizing the similarity score between the two sequences. The design consists of two main stages: matrix filling and traceback. In the matrix filling stage, the design computes the similarity scores between the input sequences and stores them in a 2D matrix M. In the traceback stage, the design traces back the optimal alignment path from the filled matrix and generates the aligned sequences.

Top-Level Function: `needwun`

Inputs:

- `SEQA`: a 1D array of characters representing the first input sequence, with a length of ALEN (128) characters.
- `SEQB`: a 1D array of characters representing the second input sequence, with a length of BLEN (128) characters.
- `alignedA`: a 1D array of characters to store the aligned sequence A, with a length of ALEN+BLEN characters.
- `alignedB`: a 1D array of characters to store the aligned sequence B, with a length of ALEN+BLEN characters.
- `M`: a 2D array of integers to store the similarity scores, with a size of (ALEN+1) x (BLEN+1).
- `ptr`: a 2D array of characters to store the traceback pointers, with a size of (ALEN+1) x (BLEN+1).

Outputs:

- `alignedA`: the aligned sequence A, stored in the input array.
- `alignedB`: the aligned sequence B, stored in the input array.

Important Data Structures and Data Types:

- `M`: a 2D array of integers to store the similarity scores, with a size of (ALEN+1) x (BLEN+1). Each element in the array represents the maximum similarity score between the subsequences of SEQA and SEQB.
- `ptr`: a 2D array of characters to store the traceback pointers, with a size of (ALEN+1) x (BLEN+1). Each element in the array represents the direction of the optimal alignment path.

Sub-Components:

- `init_row` and `init_col`: initialization loops to set the boundary values of the matrix M.
- `fill_out` and `fill_in`: nested loops to fill the matrix M with similarity scores.
- `trace`: a loop to trace back the optimal alignment path from the filled matrix and generate the aligned sequences.
- `pad_a` and `pad_b`: loops to pad the aligned sequences with underscores to ensure a fixed length of ALEN+BLEN characters.