## hotspot

Simulates transient heat conduction on a `GRID_ROWS`$\times$`GRID_COLS` chip grid using an
explicit finite-difference thermal RC model, run for `SIM_TIME` discrete time steps, as in the
Rodinia `hotspot` benchmark.

It takes the following as inputs,

- `temp`: `GRID_ROWS`$\times$`GRID_COLS` array, the initial per-cell temperature.
- `power`: `GRID_ROWS`$\times$`GRID_COLS` array, the per-cell power dissipation, held fixed
  across all `SIM_TIME` steps.

and gives the following as output:

- `temp`: overwritten in place with the temperature grid after `SIM_TIME` update steps (the
  `result` argument is used only as scratch space for intermediate steps).

Every one of the `SIM_TIME` steps applies the same update to every cell $(r,c)$:

$$
temp'(r,c) = temp(r,c) + Cap_1 \Big( power(r,c) + Rx_1 \cdot \nabla_x + Ry_1 \cdot \nabla_y + Rz_1 \big(80 - temp(r,c)\big) \Big)
$$

where $\nabla_x$ is the sum of horizontal-neighbor temperature differences (left + right minus
twice the center, using only the neighbors that exist) and $\nabla_y$ is the analogous vertical
sum; a cell missing a neighbor (grid border) simply omits that neighbor's term rather than
substituting a value (an insulated/Neumann boundary). $Rx_1, Ry_1, Rz_1, Cap_1$ are fixed
constants derived from the chip's physical parameters (dimensions, silicon heat capacity and
conductivity) and a numerically stable time-step size; $80$ is the ambient temperature.
