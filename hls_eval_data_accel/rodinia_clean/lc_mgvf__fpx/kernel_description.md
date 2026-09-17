## lc_mgvf

Iteratively smooths a "motion gradient vector flow" (MGVF) field by anisotropic diffusion,
used in active-contour cell tracking in the Rodinia leukocyte-tracking benchmark.

It takes the following as inputs,

- `imgvf`: `GRID_ROWS`$\times$`GRID_COLS` array, the initial vector-flow field.
- `I`: `GRID_ROWS`$\times$`GRID_COLS` array, a fixed external-force image, unchanged across
  iterations.

and gives the following as output:

- `imgvf`: overwritten in place with the field after `ITERATION` diffusion sweeps (the
  `result` argument is used only as scratch space for intermediate sweeps).

One sweep computes, at every pixel $(i,j)$, its 8-connected neighbor differences (each
neighbor minus the pixel's current value; a neighbor across the image border contributes 0):

$$
vHe(i,j) = old(i,j) + \frac{\mu}{\lambda} \sum_{\text{8 neighbors}} H(\Delta) \cdot \Delta
$$

where $\Delta$ is a neighbor difference, $\mu = 0.5$, $\lambda = 8\mu+1 = 5$, and $H$ is a
soft direction-selecting step function: $H(\Delta)=1$ if $\Delta > 10^{-4}$, $H(\Delta)=0.5$ if
$|\Delta| \le 10^{-4}$, and $H(\Delta)=0$ if $\Delta < -10^{-4}$ (diffusion flows only from
higher or equal neighbors, never from lower ones). The new value is then:

$$
new(i,j) = vHe(i,j) - \frac{1}{\lambda}\, I(i,j)\,\big(vHe(i,j) - I(i,j)\big)
$$

`ITERATION` such sweeps are applied in sequence, each reading the previous sweep's entire grid.
