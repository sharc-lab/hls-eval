/* *
 * @file       keccak_hls.c
 * @brief      HLS-based Keccak implementation in C
 * @project    ARC-2015 HLS SHA-3
 * @author     Ekawat (ice) Homsirikamol
 * @version    1.0
 * @copyright  Copyright (c) 2014 Cryptographic Engineering Research Group
 *             ECE Department, George Mason University Fairfax, VA, U.S.A.
 *             All rights Reserved.
 * @license    This project is released under the GNU Public License.
 *             The license and distribution terms for this file may be
 *             found in the file LICENSE in this distribution or at
 *             http://www.gnu.org/licenses/gpl-3.0.txt
 * @note       This is publicly available encryption source code that falls
 *             under the License Exception TSU (Technology and software-
 *             —unrestricted)
 */
 
#include <string.h>
#include <stdio.h>
#include "ap_cint.h"

#define DEBUG_ROUND 1
#define NB_ROUNDS 24

typedef uint64 UINT64;

#define index(x, y) (((x)%5)+5*((y)%5))
#define ROL64(a, offset) ((offset != 0) ? ((((UINT64)a) << offset) ^ (((UINT64)a) >> (64-offset))) : a)

void printState(UINT64 state[25])
{
  int x, y;
  printf("  ");
  for (x = 0; x < 5; x++)
  {
    for (y = 0; y < 5; y++)
    {
      printf("%016llX ", state[x*5+y]);
    }
    printf("\n  ");
  }
  printf("\n");
}

void theta(UINT64 A[25], UINT64 B[25])
{
  unsigned int x, y;
  UINT64 C[5], D[5];

  for(x=0; x<5; x++) 
  {
#pragma HLS UNROLL      
    C[x] = A[index(x, 0)]^A[index(x, 1)]^A[index(x, 2)]^A[index(x, 3)]^A[index(x, 4)];
  }
  for(x=0; x<5; x++)
  {
#pragma HLS UNROLL
    D[x] = ROL64(C[(x+1)%5], 1) ^ C[(x+4)%5];
  }

  for(x=0; x<5; x++)
  {
#pragma HLS UNROLL
    for(y=0; y<5; y++)
    {
#pragma HLS UNROLL
      B[index(x, y)] = A[index(x, y)] ^ D[x];
    }
  }
}

void rho(UINT64 A[25])
{
  static const unsigned int KeccakRhoOffsets[25] = {
      0,  1, 62, 28, 27,
     36, 44,  6, 55, 20,
      3, 10, 43, 25, 39,
     41, 45, 15, 21,  8,
     18,  2, 61, 56, 14
  };
  unsigned int x, y;

  for(x=0; x<5; x++) 
  {
#pragma HLS UNROLL
    for(y=0; y<5; y++)
    {
#pragma HLS UNROLL
      A[index(x, y)] = ROL64(A[index(x, y)], KeccakRhoOffsets[index(x, y)]);
    }
  }
}

void pi(UINT64 A[25])
{
  unsigned int x, y;
  UINT64 tempA[25];

  for(x=0; x<5; x++) 
  {
#pragma HLS UNROLL    
    for(y=0; y<5; y++)
    {
#pragma HLS UNROLL      
      tempA[index(x, y)] = A[index(x, y)];
    }
  }
  for(x=0; x<5; x++) 
  {
#pragma HLS UNROLL
    for(y=0; y<5; y++)
    {
#pragma HLS UNROLL
      A[index(0*x+1*y, 2*x+3*y)] = tempA[index(x, y)];
    }
  }
}

void chi(UINT64 A[25])
{
  unsigned int x, y;
  UINT64 C[25];

  for(y=0; y<5; y++) 
  { 
#pragma HLS UNROLL
    for(x=0; x<5; x++)
    {
#pragma HLS UNROLL       
     C[index(x, y)] = A[index(x, y)] ^ ((~A[index(x+1, y)]) & A[index(x+2, y)]);
    }
  }
  
  for(x=0; x<25; x++)
  {
#pragma HLS UNROLL    
    A[x] = C[x];
  }
}

void iota(UINT64 A[25], unsigned int indexRound)
{
  static const UINT64 KeccakRoundConstants[32] = {
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000
  };
#pragma HLS RESOURCE variable=KeccakRoundConstants core=ROM_1P_1S
  A[index(0, 0)] ^= KeccakRoundConstants[indexRound];
}

void keccak(UINT64 data[17], UINT64 output[4], uint1 last)
{
#pragma HLS INTERFACE ap_hs port=output
  int i;
  uint8 round;
  static UINT64 state[25] = {
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0
  };
  UINT64 tmp_state[25];
  
#pragma HLS ARRAY_RESHAPE variable=data complete dim=1
#pragma HLS ARRAY_RESHAPE variable=output complete dim=1  
#pragma HLS ARRAY_RESHAPE variable=state complete dim=1  
#pragma HLS ARRAY_RESHAPE variable=tmp_state complete dim=1
  
  /* State ^ Data */\
  for (i = 0; i < 17; i++)
  {
#pragma HLS UNROLL
    state[i] ^= data[i];
  }
  
  /* Main round */
  for(round = 0; round < NB_ROUNDS; round++) 
  {
#if DEBUG_ROUND
    printf("Input to round %d:\n", round);
    printState(state);
#endif
    theta(state, tmp_state);
#if DEBUG_ROUND
    printf("  After theta:\n");
    printState(tmp_state);
#endif
    rho(tmp_state);
#if DEBUG_ROUND
    printf("  After rho:\n");
    printState(state);
#endif
    pi(tmp_state);
#if DEBUG_ROUND
    printf("  After pi:\n");
    printState(tmp_state);
#endif
    chi(tmp_state);
#if DEBUG_ROUND
    printf("  After chi:\n");
    printState(tmp_state);
#endif
    iota(tmp_state, round);
#if DEBUG_ROUND
    printf("  After iota:\n");
    printState(tmp_state);
#endif
    if ((round == NB_ROUNDS-1) && (last == 1))
    {
      for (i = 0; i < 4; i++)
      {
#pragma HLS UNROLL
        output[i] = tmp_state[i];
      }
      for (i = 0; i < 25; i++)
      {
#pragma HLS UNROLL
        state[i] = 0;
      }
    }
    else
      for (i = 0; i < 25; i++)
      {
#pragma HLS UNROLL
        state[i] = tmp_state[i];
      }
  }
}
