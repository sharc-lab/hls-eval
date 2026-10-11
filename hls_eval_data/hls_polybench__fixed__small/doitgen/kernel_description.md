## doitgen

Kernel of Multiresolution ADaptive NumErical Scientific Simulation (MADNESS). The kernel is taken from the modified version used by You et al.
It takes the following as inputs,

- $A: R \times Q \times S$ array
- $x: P \times S$ array

and gives the following as output:

- $A_{out}: R \times Q \times P$ array

where $A_{out}(r, q, p) = \sum_{s=0}^{S-1} A(r, q, s) x(p, s)$

Note that the output $A_{out}$ is to be stored in place of the input array $A$ in the original code. Although it is not mentioned anywhere, the computation does not make sense if $P \neq S$.
Interface mapping and typed storage: R=25,Q=20,P=S=30. x(p,s) denotes C4[s][p], not C4[p][s]. For each r in increasing order and each q in increasing order, preserve the entry A[r][q][:] while computing all p results. For each p in increasing order, initialize a t_ap_fixed accumulator to zero, then accumulate A[r][q][s]*C4[s][p] for s=0..29 in increasing order, storing into t_ap_fixed after every addition. After every p is computed, copy all results into A[r][q][:]. Use the declared AP type and modes at those conversion points; C4 is preserved.
The sum argument is workspace. Its call-entry values must not influence A, and its final contents are unspecified; it is not an additional output obligation. The sole defined result is all of A.

Original numeric type: t_ap_fixed is exactly ap_fixed<32,16>, with the original SDK default AP_TRN quantization, AP_WRAP overflow and N=0 template settings. Retain that declared width, integer width and those conversion/storage points; the observable stored result is compared by its 32 raw bits.
