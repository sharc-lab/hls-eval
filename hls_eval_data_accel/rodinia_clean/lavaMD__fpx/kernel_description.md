## lavaMD

Computes short-range pairwise interaction forces and potentials between particles arranged in
a regular 3D grid of "boxes," as in the Rodinia `lavaMD` molecular-dynamics benchmark. The
domain is `DIMENSION_1D`$^3$ boxes, each holding `NUMBER_PAR_PER_BOX` particles; every particle
interacts only with particles in its own box and its 26 geometric neighbor boxes (a full
3x3x3 neighborhood). The input particle array is supplied already surrounded by one extra
layer of empty (zero-valued) boxes around the whole domain, so that every real box has a
complete neighborhood available to read.

It takes the following as inputs,

- `pos_i`: padded array of 4-vectors, one per particle (real and padding), laid out box-major.
  Each 4-vector is $(v, x, y, z)$ where $(x,y,z)$ is the particle's position and $v$ is a
  scalar potential/charge-like parameter of the particle.
- `q_i`: padded array of one scalar charge factor per particle, matching `pos_i`'s layout.

and gives the following as output:

- `pos_o`: unpadded array of one 4-vector accumulator per real particle: index $v$ receives the
  accumulated potential, indices $x,y,z$ receive the accumulated force components.

For every real particle $a$ and every particle $b$ in $a$'s own box or one of its 26 neighbor
boxes (including $b=a$, which contributes to the potential but not the force):

$$
r^2 = v_a + v_b - (x_a x_b + y_a y_b + z_a z_b), \qquad u = A_2 \, r^2, \qquad A_2 = 2\,\alpha^2,\ \alpha = 0.5
$$

$$
v_{ij} \approx 1 - u + \tfrac12 u^2 - \tfrac16 u^3 + \tfrac1{24} u^4 \quad \text{(a 4th-order Taylor approximation of } e^{-u} \text{)}
$$

$$
f_s = 2 v_{ij}, \qquad (d_x,d_y,d_z) = (x_a,y_a,z_a) - (x_b,y_b,z_b), \qquad (f_x,f_y,f_z) = f_s \cdot (d_x,d_y,d_z)
$$

and accumulate into `pos_o[a]`: $v \mathrel{+}= q_b \, v_{ij}$, and
$(x,y,z) \mathrel{+}= q_b \, (f_x,f_y,f_z)$.
