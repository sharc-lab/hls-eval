#pragma once
/*
 * Portable stand-in for Xilinx Vitis HLS's ap_cint.h.
 *
 * The real ap_cint.h defines uintN/intN via __attribute__((bitwidth(N))),
 * a compiler extension only understood by Xilinx's internal HLS compiler
 * driver (not by a plain clang/gcc invocation, and not needed for C
 * simulation here). Every use of these types in this kernel is a boolean
 * flag, a small round counter, or (in JH) a nibble container already
 * holding a value in range - never an operation whose correctness depends
 * on wraparound at the exact narrow bit width - so mapping them onto
 * standard fixed-width integers from <stdint.h> is behaviorally
 * equivalent for C simulation, and is verified by each testbench's
 * known-answer test vectors.
 */
#include <stdint.h>

typedef uint8_t  uint1;
typedef uint8_t  uint4;
typedef uint8_t  uint5;
typedef uint8_t  uint8;
typedef uint16_t uint16;
typedef uint32_t uint32;
typedef uint64_t uint64;
