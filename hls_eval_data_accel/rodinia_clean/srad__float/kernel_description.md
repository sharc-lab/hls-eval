## srad

Speckle Reducing Anisotropic Diffusion (SRAD): iteratively smooths a `ROWS`$\times$`COLS`
image while preserving edges, run for `NITER` update passes, as in the Rodinia `srad`
benchmark.

It takes as input,

- `J`: the image, supplied as a $(\text{ROWS}+3)\times\text{COLS}$ buffer — one row of padding
  above and two below the real `ROWS`$\times$`COLS` image, all padding rows set to 0 and unused
  by the computation.

and gives as output:

- `Jout`: the $(\text{ROWS}+3)\times\text{COLS}$ image after `NITER` diffusion passes (same
  padding layout as `J`).

One diffusion pass computes, at every interior pixel $(i,j)$, its 4-connected neighbor
differences $d_N, d_S, d_W, d_E$ (neighbor minus the pixel's current value $J_c$; 0 at an image
border in that direction), then the local diffusion coefficient (equ. 33 of the SRAD
algorithm):

$$
G^2 = \frac{d_N^2+d_S^2+d_W^2+d_E^2}{J_c^2}, \qquad
L = \frac{d_N+d_S+d_W+d_E}{J_c}, \qquad
q^2 = \frac{\tfrac12 G^2 - \tfrac{1}{16}L^2}{\left(1+\tfrac14 L\right)^2}
$$

$$
c = \operatorname{clamp}\!\left(\frac{1}{1 + \dfrac{q^2 - q_0^2}{q_0^2(1+q_0^2)}},\ 0,\ 1\right)
$$

where $q_0^2$ is a fixed constant ($0.0870038941502571$), not recomputed from the image. The
pixel is then updated (equ. 61), using this pixel's own coefficient $c$ for the north and west
terms, and the coefficient computed at the pixel below / to the right for the south and east
terms respectively:

$$
Jout(i,j) = J(i,j) + \frac{\lambda}{4}\left(c_N d_N + c_S d_S + c_W d_W + c_E d_E\right), \qquad \lambda = 0.5
$$

`NITER` such passes are applied in sequence, each reading the previous pass's entire image.
