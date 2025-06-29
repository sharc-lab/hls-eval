#include <stdint.h>

/*
Implemenataion based on:
A. Danalis, G. Marin, C. McCurdy, J. S. Meredith, P. C. Roth, K. Spafford, V.
Tipparaju, and J. S. Vetter. The scalable heterogeneous computing (shoc)
benchmark suite. In Proceedings of the 3rd Workshop on General-Purpose
Computation on Graphics Processing Units, 2010.
*/

#include <stdio.h>
#include <stdlib.h>

#define TYPE double

// Problem Constants
#define nAtoms 256
#define maxNeighbors 16
// LJ coefficients
#define lj1 1.5
#define lj2 2.0

void md_kernel(
    TYPE force_x[nAtoms],
    TYPE force_y[nAtoms],
    TYPE force_z[nAtoms],
    TYPE position_x[nAtoms],
    TYPE position_y[nAtoms],
    TYPE position_z[nAtoms],
    int32_t NL[nAtoms * maxNeighbors]);
