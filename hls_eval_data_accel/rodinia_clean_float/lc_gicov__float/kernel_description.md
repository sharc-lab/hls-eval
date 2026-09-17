## lc_gicov

Computes, for every interior pixel of a gradient image, a "Gradient Inverse Coefficient of
Variation" (GICOV) score used to detect circular cell-like edges, as in the Rodinia
leukocyte-tracking benchmark.

It takes the following as inputs,

- `grad_x`, `grad_y`: `GRID_ROWS`$\times$`GRID_COLS` arrays, the horizontal and vertical
  components of the image gradient at every pixel.

and gives the following as output:

- `result`: `GRID_ROWS`$\times$`GRID_COLS` array. Pixels within `MAX_RADIUS` of any image edge
  are left as zero (never written); every other ("interior") pixel receives the score below.

For `NCIRCLES` $= 2$ concentric sampling circles of radius $r_k = \text{MIN\_RADIUS} + k$ for
$k = 0, 1$ (`MIN_RADIUS` $=2$), each sampled at `NPOINTS` $= 16$ points evenly spaced around the
circle (pixel offsets rounded to the nearest integer, at angles $\theta_n = 2\pi n/16$), the
directional gradient at sample point $n$ of circle $k$, located at $(i,j) + r_k(\cos\theta_n,\sin\theta_n)$
rounded to the nearest pixel, is:

$$
Grad_k(n) = grad\_x \cdot \cos\theta_n + grad\_y \cdot \sin\theta_n
$$

Compute the mean and the unbiased (dividing by $N\!-\!1$) sample variance of $Grad_k(0..15)$.
Circle $k$'s candidate score is $mean_k / \sqrt{var_k}$, retained as the pixel's output only if
$mean_k^2 / var_k$ is the largest such ratio seen so far among $k=0,1$ at that pixel (circle
$k=0$ is evaluated first).
