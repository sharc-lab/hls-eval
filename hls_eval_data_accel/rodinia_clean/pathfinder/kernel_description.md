## pathfinder

Finds the minimum-cost path sum reaching each column of the last row of a
`ROWS`$\times$`COLS` weighted grid, moving strictly one row down at a time and allowed to step
to the same or an adjacent column, as in the Rodinia `pathfinder` benchmark.

It takes as input,

- `J`: `ROWS`$\times$`COLS` array (row-major); row 0 gives the initial per-column costs.

and gives as output:

- `Jout`: vector of length `COLS`, the minimum path-sum reaching each column of the last row.

Let $running$ be initialized to row 0 of $J$. For each row $t = 1, \ldots, \text{ROWS}-1$, and
each column $n$:

$$
running'(n) = J(t, n) + \min\big(running(n-1),\, running(n),\, running(n+1)\big)
$$

using $running$ from the previous row throughout (a neighbor outside $[0,\text{COLS})$ is
omitted from the min). After processing row `ROWS-1`, `Jout` is the resulting $running$ array.
