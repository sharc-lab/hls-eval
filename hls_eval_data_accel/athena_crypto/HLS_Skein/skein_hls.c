/* *
 * @file       skein_hls.h
 * @brief      Header file of HLS-based Skein implementation in C
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

#define DEBUG_ROUND 0
#define NB_ROUNDS 19

typedef uint64 UINT64;

void printState(UINT64 state[8])
{
  int x;
  printf("  ");
  for (x = 0; x < 8; x++)
  {
    printf("%016llX ", state[7-x]);
    if ((x+1) % 4 == 0) printf("\n  ");
  }
  printf("\n");
}

void mix_and_permute(UINT64 state[8], int subround, uint1 is_lo)
{
#pragma HLS INLINE
  const static int rot[4][8] = {
      {46, 36, 19, 37, 39, 30, 34, 24},
      {33, 27, 14, 42, 13, 50, 10, 17},
      {17, 49, 36, 39, 25, 29, 39, 43},
      {44,  9, 54, 56,  8, 35, 56, 22}
  };
  const static int permute[8] = {
     2, 1, 4, 7, 6, 5, 0, 3
  };

  int i;
  UINT64 temp[8];

#define ROL64(a, offset) ((((UINT64)a) << offset) ^ (((UINT64)a) >> (64-offset)))

  /* Mix */
  for (i=0 ;i<4; i++)
  {
#pragma HLS UNROLL
    temp[i*2+0] = state[i*2+0] + state[i*2+1];
    if (is_lo == 0)
      temp[i*2+1] = ROL64(state[i*2+1], rot[subround][i]);
    else
      temp[i*2+1] = ROL64(state[i*2+1], rot[subround][i+4]);
    temp[i*2+1] ^= temp[i*2+0];
  }

  /* Permute */
  for (i=0; i<8; i++)
  {
#pragma HLS UNROLL
    state[i] = temp[permute[i]];
  }
}

void getRoundKey(UINT64 keyState[8], uint64 tweak[3], uint5 subround, UINT64 subkey[8])
{
#pragma HLS INLINE
  subkey[7] = keyState[7] + (UINT64) subround;
  subkey[6] = keyState[6] + tweak[1];
  subkey[5] = keyState[5] + tweak[0];
  subkey[4] = keyState[4];
  subkey[3] = keyState[3];
  subkey[2] = keyState[2];
  subkey[1] = keyState[1];
  subkey[0] = keyState[0];
}

void skein(UINT64 data[8], UINT64 output[4], uint1 firstBlock,  uint1 lastBlock, uint32 size)
{
#pragma HLS INTERFACE ap_hs port=output

  int i;
  int total_round;
  uint8 round;
  uint5 subround;
  uint1 is_lo;

  static UINT64 state[8];
  UINT64 tmpState[8];
  static UINT64 tweak[3];
  UINT64 initTweak[3];

  UINT64 newTweak[3];

  static UINT64 byteCounter = 0;
  UINT64 initByteCounter;
  

  UINT64 enableData =   0xFFFFFFFFFFFFFFFF;
  static UINT64 keyState[8];
  UINT64 initKeyState[8];
  UINT64 keyInjState[8];
  UINT64 keyIn[8];
  UINT64 keyNew[8];
  UINT64 keyPar;
  static UINT64 subkey[8];

#pragma HLS ARRAY_RESHAPE variable=data complete dim=1
#pragma HLS ARRAY_RESHAPE variable=output complete dim=1  
#pragma HLS ARRAY_RESHAPE variable=tweak complete dim=1
#pragma HLS ARRAY_RESHAPE variable=initTweak complete dim=1
#pragma HLS ARRAY_RESHAPE variable=newTweak complete dim=1
#pragma HLS ARRAY_RESHAPE variable=state complete dim=1
#pragma HLS ARRAY_RESHAPE variable=keyIn complete dim=1
#pragma HLS ARRAY_RESHAPE variable=keyInjState complete dim=1
#pragma HLS ARRAY_RESHAPE variable=tmpState complete dim=1
#pragma HLS ARRAY_RESHAPE variable=keyState complete dim=1
#pragma HLS ARRAY_RESHAPE variable=subkey complete dim=1
#pragma HLS ARRAY_RESHAPE variable=keyNew complete dim=1
  
  if (lastBlock == 1)
    total_round = NB_ROUNDS*2;
  else
    total_round = NB_ROUNDS;


  /* Initial values */\
  for (i = 0; i < 8; i++)
  {
#pragma HLS UNROLL
    state[i] = data[i];
  }
  
  if (firstBlock == 1)
    {
      initKeyState[0] = 0xCCD044A12FDB3E13;
      initKeyState[1] = 0xE83590301A79A9EB;
      initKeyState[2] = 0x55AEA0614F816E6F;
      initKeyState[3] = 0x2A2767A4AE9B94DB;
      initKeyState[4] = 0xEC06025E74DD7683;
      initKeyState[5] = 0xE7A436CDC4746251;
      initKeyState[6] = 0xC36FBAF9393AD185;
      initKeyState[7] = 0x3EEDBA1833EDFC13;
      initByteCounter = 0;
      enableData      = 0xFFFFFFFFFFFFFFFF;
    }
  else
    {
      for (i=0; i<8; i++)
      {
#pragma HLS UNROLL
          initKeyState[i] = keyState[i];
      }
      initByteCounter = byteCounter;
    }

  initTweak[0] = initByteCounter + size;
  initTweak[1] = 0x3000000000000000 | (((UINT64) firstBlock) << 62) | (((UINT64) lastBlock) << 63);
  initTweak[2] = initTweak[0] ^ initTweak[1];

#if DEBUG_ROUND
  printf("==NEW BLOCK==\n");
  printf("  ::Initial Keystate::\n");
  printState(keyState);
  printf("  ::Initial Tweak::\n");
  printf("  %016llX %016llX %016llX\n\n", initTweak[2], initTweak[1],initTweak[0]);
#endif
  keyPar = 0x1BD11BDAA9FC1A22;
  for (i=0; i<8; i++)
  {
#pragma HLS UNROLL
    keyPar  ^= initKeyState[i];
  }


  // Assign value to registers
  getRoundKey(initKeyState, initTweak, 0, subkey);
  for (i=0; i<7; i++)
  {
#pragma HLS UNROLL
    keyState[i] = initKeyState[i+1];
  }
  keyState[7] = keyPar;
  tweak[0] = initTweak[1];
  tweak[1] = initTweak[2];
  tweak[2] = initTweak[0];
  byteCounter = initTweak[0];

  /* Main round */
  for(round = 0; round < total_round; round++)
  {
    /* Control computation */
    if (round > NB_ROUNDS-2)
      subround = (round + 1) - NB_ROUNDS;
    else
      subround = (round + 1);

    is_lo = round % 2;
    /* Real hardware uint1 truncates ~ to 1 bit; our portable uint1 stand-in
       (see ap_cint.h) is wider, so mask explicitly to keep the 0/1 toggle. */
    if (round >= NB_ROUNDS) is_lo = (~is_lo) & 0x1;

    /* Core computation (Combinational operations) */
#if DEBUG_ROUND
    if ((round == NB_ROUNDS-1) || (round == NB_ROUNDS*2-1))
      printf("!!!Last Round!!!\n");
    printf("Input to round %d:\n", round);
    printState(state);

    printf("  ::Round subkey::\n");
    printState(subkey);
#endif
    for (i=0; i<8; i++)
    {
#pragma HLS UNROLL
      keyInjState[i]  = state[i] + subkey[i];
      tmpState[i]  = keyInjState[i];
    }
#if DEBUG_ROUND
    printf("  ::After KeyInj::\n");
    printState(tmpState);
#endif
    mix_and_permute(tmpState,0,is_lo);
    mix_and_permute(tmpState,1,is_lo);
    mix_and_permute(tmpState,2,is_lo);
    mix_and_permute(tmpState,3,is_lo);
#if DEBUG_ROUND
    printf("  ::After Mix & Permute::\n");
    printState(tmpState);
#endif

    /* Compute next subkey */
    for(i=0; i<8; i++)
    {
#pragma HLS UNROLL
      keyNew[i] = keyInjState[i] ^ (data[i] & enableData);
    }

    if (round == NB_ROUNDS-1)
      for(i=0; i<8; i++)
      {
#pragma HLS UNROLL
        keyIn[i] = keyNew[i];
      }
    else
      for(i=0; i<8; i++)
      {
#pragma HLS UNROLL
        keyIn[i] = keyState[i];
      }

#if DEBUG_ROUND
    printf("  ::enableData => %016llX\n", enableData);
    printf("  ::keyNew::\n");
    printState(keyNew);
    printf("  ::keyIn::\n");
    printState(keyIn);
#endif

    getRoundKey(keyIn, tweak, subround, subkey);


    keyPar = 0x1BD11BDAA9FC1A22;
    for(i=0; i<8; i++)
    {
#pragma HLS UNROLL
      keyPar    ^= keyIn[i];
    }

    newTweak[0] = tweak[1];
    newTweak[1] = tweak[2];
    newTweak[2] = tweak[0];

    /* ===================== */
    /* Sequential operations */
    /* ===================== */
    // Update tweak
    if ((round == NB_ROUNDS-2) && (total_round > NB_ROUNDS))
    {
      tweak[0] = 0x0000000000000008;
      tweak[1] = 0xFF00000000000000;
      tweak[2] = 0xFF00000000000008;
    }
    else
    {
      tweak[0] = newTweak[0];
      tweak[1] = newTweak[1];
      tweak[2] = newTweak[2];
    }

    // Output
    if (round == NB_ROUNDS*2-1)
      for (i=0; i<4; i++)
      {
  #pragma HLS UNROLL
        output[i] = keyNew[i];
      }

    // Update keyState
    if ((round == NB_ROUNDS-1) && (total_round == NB_ROUNDS))
      for(i=0; i<8; i++)
      {
#pragma HLS UNROLL
        keyState[i] = keyIn[i];
      }
    else
    {
      for(i=0; i<7; i++)
      {
#pragma HLS UNROLL
        keyState[i] = keyIn[i+1];
      }
      keyState[7] = keyPar;
    }

    // State
    if (round == NB_ROUNDS-1)
      for(i=0; i<8; i++)
      {
#pragma HLS UNROLL
        state[i]     = 0;
      }
    else
      for(i=0; i<8; i++)
      {
#pragma HLS UNROLL
        state[i]    = tmpState[i];
      }

    // Enable data register
    if ((round == NB_ROUNDS-1) && (total_round == NB_ROUNDS*2))
      enableData = 0;
  }
}
