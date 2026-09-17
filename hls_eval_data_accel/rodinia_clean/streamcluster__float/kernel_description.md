## streamcluster

Evaluates, for a batch of points, the local-search "gain" of opening a new candidate cluster
center in the PAM/k-median local-search step of the Rodinia `streamcluster` benchmark: for
each point, whether it would be cheaper to reassign it to the new center, and if not, how much
its current center would save by closing.

It takes the following as inputs,

- `coord`: `BATCH_SIZE`$\times$`DIM` array (row-major), the coordinates of every point.
- `weight`: vector of length `BATCH_SIZE`, a per-point weight.
- `cost`: vector of length `BATCH_SIZE`, each point's current assignment cost.
- `target`: vector of length `DIM`, the coordinates of the candidate new center $x$.
- `assign`: vector of length `BATCH_SIZE`, the index of the center each point is currently
  assigned to.
- `center_table`: a lookup table mapping a point index that is itself an open center to a
  compact index in $[0, \text{numcenter})$ used to index `work_mem`.
- `num`, `numcenter`: the batch size and the number of currently open centers.

and gives the following as outputs:

- `switch_membership`: vector of length `BATCH_SIZE`; set to 1 for every point that should
  switch to the new center $x$ (left unchanged, 0, otherwise).
- `work_mem`: indexed by `center_table[assign[i]]`; decremented, for every point that does
  *not* switch to $x$, by that point's potential cost saving.
- `cost_of_opening_x`: a single accumulator, increased by the cost saving of every point that
  *does* switch to $x$.

For every point $i$:

$$
cost_i = weight(i) \cdot \lVert coord(i) - target \rVert^2 - cost(i)
$$

If $cost_i < 0$: set $switch\_membership(i) = 1$ and add $cost_i$ to `cost_of_opening_x`.
Otherwise: subtract $cost_i$ from $work\_mem\big(center\_table(assign(i))\big)$.
