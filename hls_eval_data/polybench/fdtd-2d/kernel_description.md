Kernel Description:
The `kernel_fdtd_2d` kernel implements the Simplified Finite-Difference Time-Domain (FDTD) method for 2D data, which models electric and magnetic fields based on Maxwell's equations. In particular, the polarization used here is ( TE^z ); Transverse Electric in ( z ) direction. It is a stencil involving three variables, ( Ex ), ( Ey ), and ( Hz ). ( Ex ) and ( Ey ) are electric fields varying in ( x ) and ( y ) axes, where ( Hz ) is the magnetic field along ( z ) axis. Fields along other axes are either zero or static, and are not modeled.

$$
\begin{align*}
Hz_{(i,j)}^{t} &= C_{hzh} Hz_{(i,j)}^{t-1} + C_{hze} \left(Ex_{(i,j+1)}^{t-1} - Ex_{(i,j)}^{t-1} - Ey_{(i+1,j)}^{t-1} + Ey_{(i,j)}^{t-1}\right) \\
Ex_{(i,j)}^{t} &= C_{exe} Ex_{(i,j)}^{t-1} + C_{exh} \left(Hz_{(i,j)}^{t} - Hz_{(i,j-1)}^{t}\right) \\
Ey_{(i,j)}^{t} &= C_{eye} Ey_{(i,j)}^{t-1} + C_{eyh} \left(Hz_{(i,j)}^{t} - Hz_{(i-1,j)}^{t}\right)
\end{align*}
$$

Variables ( C_{xxx} ) are coefficients that may be different depending on the location within the discretized space. In PolyBench, it is simplified as scalar coefficients.

---

Top-Level Function: `kernel_fdtd_2d`

Complete Function Signature of the Top-Level Function:
`void kernel_fdtd_2d(double ex[20][30], double ey[20][30], double hz[20][30], double _fict_[20]);`

Inputs:
- `ex`: a 2D array of size 20x30, representing the electric field in the x-direction.
- `ey`: a 2D array of size 20x30, representing the electric field in the y-direction.
- `hz`: a 2D array of size 20x30, representing the magnetic field in the z-direction.
- `_fict_`: a 1D array of size 20, representing the fictitious source term.

Outputs:
- `ex`: the updated electric field in the x-direction.
- `ey`: the updated electric field in the y-direction.
- `hz`: the updated magnetic field in the z-direction.

Important Data Structures and Data Types:
- `double[20][30]`: a 2D array of size 20x30, used to represent the electric and magnetic fields.
- `double[20]`: a 1D array of size 20, used to represent the fictitious source term.

Sub-Components:
- None