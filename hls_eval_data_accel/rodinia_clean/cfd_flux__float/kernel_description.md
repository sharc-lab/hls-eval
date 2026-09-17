## cfd_flux

Computes one evaluation of the numerical flux (the per-cell residual contribution) for an
unstructured finite-volume solver of the compressible Euler equations, as in the Rodinia/CFD
`compute_flux` kernel. There are `SIZE` mesh elements; each has `NVAR = 5` conserved flow
variables (density, the 3 components of momentum, and density $\times$ energy) and `NNB = 4`
neighboring faces.

It takes the following as inputs,

- `elements_surrounding_elements`: `SIZE`$\times$`NNB` array. For element $i$ and face $f$, gives
  the index of the neighboring element across that face, or a special code: $-1$ marks a
  solid-wall boundary face, $-2$ marks a far-field boundary face.
- `normals`: `SIZE`$\times$`NNB`$\times$`NDIM` array (`NDIM = 3`), the outward face-normal vector
  (scaled by face area) for each element/face.
- `variables`: `SIZE`$\times$`NVAR` array, the current conserved state (density, momentum$_{x,y,z}$,
  density$\cdot$energy) of every element.
- `fc_momentum_x`, `fc_momentum_y`, `fc_momentum_z`: `SIZE`$\times$`NDIM` arrays, the precomputed
  convective flux vector associated with the momentum-$x$/$y$/$z$ equation of every element.
- `fc_density_energy`: `SIZE`$\times$`NDIM` array, the precomputed convective flux vector for the
  energy equation of every element.

and gives the following as output:

- `result`: `SIZE`$\times$`NVAR` array, the accumulated flux for every element's 5 conserved
  quantities.

For element $i$, derive velocity $= momentum_i / density_i$, speed$^2 = |velocity|^2$,
pressure $= (\gamma-1)(density\_energy_i - \tfrac12 \, density_i \cdot speed^2)$ with
$\gamma = 1.4$, and speed-of-sound $= \sqrt{\gamma \cdot pressure / density_i}$. Then sum a
contribution over each of the `NNB` faces:

- **Interior face** (neighbor $nb \ge 0$): a central-average flux plus an artificial-dissipation
  term. Writing $n$ for the face normal, $\lVert n\rVert$ its length, and $\alpha = 0.2$ the
  smoothing coefficient:
  $$
  \text{diss} = -\lVert n\rVert \, \alpha \, \tfrac12 \left(speed_i + speed_{nb} + c_i + c_{nb}\right)
  $$
  is added, multiplied respectively by $(density_i-density_{nb})$, $(momentum_i-momentum_{nb})$,
  and $(density\_energy_i - density\_energy_{nb})$ into the density/momentum/energy flux; and for
  each axis $a \in \{x,y,z\}$, $\tfrac12 n_a \cdot (momentum_{i,a}+momentum_{nb,a})$ is added to
  the density flux, and $\tfrac12 n_a \cdot (fc_{\cdot,i,a} + fc_{\cdot,nb,a})$ is added to each of
  the momentum/energy fluxes using that quantity's own precomputed `fc_*` vectors.
- **Wall boundary face** ($nb = -1$): only the momentum flux receives $n \cdot pressure_i$
  (density and energy flux are unaffected by this face).
- **Far-field boundary face** ($nb = -2$): the same central-average formula as the interior case,
  but using fixed far-field reference values in place of a real neighbor's state:
  density $=1.4$, momentum $=(3.016,\,0,\,0)$, density$\cdot$energy $=3.508$,
  $fc_{momentum\_x} = (3.016,\,0,\,0)$, $fc_{momentum\_y} = (0,\,1,\,0)$,
  $fc_{momentum\_z} = (0,\,0,\,1)$, $fc_{density\_energy} = (5.4096,\,0,\,0)$.

`result[i]` is the sum of these contributions over all `NNB` faces of element $i$.
