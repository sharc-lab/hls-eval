## fdtd-2d

Simplified TE-z two-dimensional FDTD kernel. Use the complete original header types and extents: ex, ey and hz are60-by80 mutable fields and _fict_ contains40 boundary values. Perform exactly40 time iterations, t=0..39.

For each iteration, execute these phases in order:
1. Assign ey[0][j] = _fict_[t] for every column j.
2. For i=1..59 and j=0..79, assign ey[i][j] = ey[i][j] - t_ap_fixed(0.5)*(hz[i][j]-hz[i-1][j]).
3. For i=0..59 and j=1..79, assign ex[i][j] = ex[i][j] - t_ap_fixed(0.5)*(hz[i][j]-hz[i][j-1]).
4. For i=0..58 and j=0..78, assign hz[i][j] = hz[i][j] - t_ap_fixed(0.7)*(ex[i][j+1]-ex[i][j]+ey[i+1][j]-ey[i][j]). The ex/ey values here are those just produced by phases2/3; hz was not changed by those phases.

Each phase scans increasing row then column. Preserve original t_ap_fixed expression types and round/overflow modes; every listed assignment stores back into that type. Coefficients are first converted to t_ap_fixed as written. Do not replace intermediate stored assignments with a full-precision real-valued solve.

Outputs: all ex, ey and hz entries after40 iterations. Entries excluded from a phase retain their previous values; ex's column0 and hz's last row/column are never updated. _fict_ is an input and is preserved. No other output or reset/state persists between calls.

Original numeric type: t_ap_fixed is exactly ap_fixed<32,16>, with the original SDK default AP_TRN quantization, AP_WRAP overflow and N=0 template settings. Retain that declared width, integer width and those conversion/storage points; the observable stored result is compared by its 32 raw bits.
