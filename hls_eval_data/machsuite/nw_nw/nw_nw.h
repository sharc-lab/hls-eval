#include <stdint.h>

#include <stdio.h>
#include <stdlib.h>

#define ALEN 128
#define BLEN 128

void needwun(
    char SEQA[ALEN],
    char SEQB[BLEN],
    char alignedA[ALEN + BLEN],
    char alignedB[ALEN + BLEN],
    int M[(ALEN + 1) * (BLEN + 1)],
    char ptr[(ALEN + 1) * (BLEN + 1)]);
