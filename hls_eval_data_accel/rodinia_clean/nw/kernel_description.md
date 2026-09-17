## nw

Global pairwise alignment of two character sequences using the Needleman-Wunsch
dynamic-programming algorithm with a linear gap penalty, as in the Rodinia `nw` benchmark.

It takes the following as inputs,

- `SEQA`: vector of `ALEN` characters.
- `SEQB`: vector of `BLEN` characters.

and gives the following as outputs:

- `alignedA`, `alignedB`: vectors of `ALEN+BLEN` characters each, the two aligned sequences.

Build an $(\text{ALEN}+1)\times(\text{BLEN}+1)$ score matrix $M$ with
$M(a,0) = a \cdot GAP$, $M(0,b) = b \cdot GAP$ ($GAP = -1$), and for $a,b \ge 1$:

$$
M(a,b) = \max\Big( M(a\!-\!1,b\!-\!1) + s\big(SEQA(a\!-\!1), SEQB(b\!-\!1)\big),\; M(a\!-\!1,b) + GAP,\; M(a,b\!-\!1) + GAP \Big)
$$

where $s(x,y) = +1$ if $x=y$ (match) and $-1$ otherwise (mismatch).

Then trace back from $(a,b) = (\text{ALEN}, \text{BLEN})$ to $(0,0)$: at each step, take
whichever of the (up to three) predecessor moves attains $M(a,b)$, preferring, in order: the
"left" move (consume one character of `SEQA`, gap in `SEQB`), then the "up" move (consume one
character of `SEQB`, gap in `SEQA`), then the diagonal move (consume one character of each).
Each step emits one character (or `-` for a gap) onto the front of `alignedA`/`alignedB` — so
characters are produced from the end of the alignment backward to the start — and any
remaining length out to `ALEN+BLEN` (past the point where both indices reach 0) is filled with
`_`.
