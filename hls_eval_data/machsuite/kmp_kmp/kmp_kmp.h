#include <stdint.h>

/*
Implementation based on http://www-igm.univ-mlv.fr/~lecroq/string/node8.html
*/

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define PATTERN_SIZE 4
#define STRING_SIZE (32411)

int kmp(
    char pattern[PATTERN_SIZE],
    char input[STRING_SIZE],
    int32_t kmpNext[PATTERN_SIZE],
    int32_t n_matches[1]);
