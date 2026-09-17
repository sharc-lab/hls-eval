## cfd_step_factor

Computes, for every element of an unstructured CFD mesh, a local explicit time-step scale
factor, as in the Rodinia/CFD `time_step` preparation kernel. There are `SIZE` elements, each
with `NVAR = 5` conserved flow variables (density, the 3 components of momentum, and
density $\times$ energy).

It takes the following as inputs,

- `variables`: `SIZE`$\times$`NVAR` array, the conserved state of every element.
- `areas`: vector of length `SIZE`, a per-element mesh geometry measure (cell area/volume).

and gives the following as output:

- `result`: vector of length `SIZE`, the step factor for every element.

For element $i$: derive velocity $= momentum_i / density_i$, speed$^2 = |velocity|^2$,
pressure $= (\gamma-1)(density\_energy_i - \tfrac12 \, density_i \cdot speed^2)$ with
$\gamma = 1.4$, and speed-of-sound $c = \sqrt{\gamma \cdot pressure / density_i}$. Then:

$$
result(i) = \frac{0.5}{\sqrt{area(i)} \cdot \left(\sqrt{speed^2} + c\right)}
$$
