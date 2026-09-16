/* *
 * @file       groestl_hls.h
 * @brief      HLS-based Groestl implementation in C
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
#include "groestl_hls.h"

#if ~__SYNTHESIS__
#define DEBUG 1
#define DEBUG_ROUND 1
#endif

static void printState(u8 *x, int size)
{
  int i;
  printf("\t");
  for (i=0; i<size; i++)
  {
    printf("%02X", x[i]);
    if ((i+1)%8 == 0) printf(" ");
    if ((i+1)%32 == 0) printf("\n\t");
  }
  printf("\n");
}

void AddRoundConstant(u8 x[ROWS*COLS], u8 round, uint1 is_q)
{
  u8 i, j;

  if (is_q == 0)
    for (i = 0; i < COLS; i++)
    {
#pragma HLS UNROLL
      x[i*8] ^= (i<<4)^round;
    }
  else
  {
    for (i = 0; i < COLS; i++)
    {
#pragma HLS UNROLL
      for (j = 0; j < ROWS-1; j++)
      {
#pragma HLS UNROLL
        x[i*8+j] ^= 0xff;
      }
    }
    for (i = 0; i < COLS; i++)
    {
#pragma HLS UNROLL
      x[i*8+ROWS-1] ^= (i<<4)^0xff^round;
    }
  }
}

void SubBytes(u8 x[ROWS*COLS], u8 y[ROWS*COLS])
{
#pragma HLS INLINE
#pragma HLS RESOURCE variable=Sbox0 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox1 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox2 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox3 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox4 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox5 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox6 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox7 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox8 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox9 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox10 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox11 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox12 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox13 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox14 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox15 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox16 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox17 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox18 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox19 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox20 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox21 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox22 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox23 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox24 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox25 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox26 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox27 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox28 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox29 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox30 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox31 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox32 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox33 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox34 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox35 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox36 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox37 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox38 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox39 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox40 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox41 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox42 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox43 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox44 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox45 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox46 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox47 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox48 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox49 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox50 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox51 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox52 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox53 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox54 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox55 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox56 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox57 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox58 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox59 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox60 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox61 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox62 core=ROM_1P_1S
#pragma HLS RESOURCE variable=Sbox63 core=ROM_1P_1S

    y[0] = Sbox0[x[0]];      y[8 ] =  Sbox8[x[8 ]];
    y[1] = Sbox1[x[1]];      y[9 ] =  Sbox9[x[9 ]];
    y[2] = Sbox2[x[2]];      y[10] = Sbox10[x[10]];
    y[3] = Sbox3[x[3]];      y[11] = Sbox11[x[11]];
    y[4] = Sbox4[x[4]];      y[12] = Sbox12[x[12]];
    y[5] = Sbox5[x[5]];      y[13] = Sbox13[x[13]];
    y[6] = Sbox6[x[6]];      y[14] = Sbox14[x[14]];
    y[7] = Sbox7[x[7]];      y[15] = Sbox15[x[15]];

    y[16] = Sbox16[x[16]];   y[24] = Sbox24[x[24]];
    y[17] = Sbox17[x[17]];   y[25] = Sbox25[x[25]];
    y[18] = Sbox18[x[18]];   y[26] = Sbox26[x[26]];
    y[19] = Sbox19[x[19]];   y[27] = Sbox27[x[27]];
    y[20] = Sbox20[x[20]];   y[28] = Sbox28[x[28]];
    y[21] = Sbox21[x[21]];   y[29] = Sbox29[x[29]];
    y[22] = Sbox22[x[22]];   y[30] = Sbox30[x[30]];
    y[23] = Sbox23[x[23]];   y[31] = Sbox31[x[31]];

    y[32] = Sbox32[x[32]];   y[40] = Sbox40[x[40]];
    y[33] = Sbox33[x[33]];   y[41] = Sbox41[x[41]];
    y[34] = Sbox34[x[34]];   y[42] = Sbox42[x[42]];
    y[35] = Sbox35[x[35]];   y[43] = Sbox43[x[43]];
    y[36] = Sbox36[x[36]];   y[44] = Sbox44[x[44]];
    y[37] = Sbox37[x[37]];   y[45] = Sbox45[x[45]];
    y[38] = Sbox38[x[38]];   y[46] = Sbox46[x[46]];
    y[39] = Sbox39[x[39]];   y[47] = Sbox47[x[47]];

    y[48] = Sbox48[x[48]];   y[56] = Sbox56[x[56]];
    y[49] = Sbox49[x[49]];   y[57] = Sbox57[x[57]];
    y[50] = Sbox50[x[50]];   y[58] = Sbox58[x[58]];
    y[51] = Sbox51[x[51]];   y[59] = Sbox59[x[59]];
    y[52] = Sbox52[x[52]];   y[60] = Sbox60[x[60]];
    y[53] = Sbox53[x[53]];   y[61] = Sbox61[x[61]];
    y[54] = Sbox54[x[54]];   y[62] = Sbox62[x[62]];
    y[55] = Sbox55[x[55]];   y[63] = Sbox63[x[63]];
}

void ShiftBytes(u8 x[ROWS*COLS], uint1 is_q)
{
  int i,j;
  u8 temp[ROWS*COLS];
  static const int Shift[2][8] = {{0,1,2,3,4,5,6,7}, {1,3,5,7,0,2,4,6}};

  if (is_q == 0)
  {
    temp[ 0] = x[ 8]; temp[ 8] = x[16]; temp[16] = x[24]; temp[24] = x[32]; temp[32] = x[40]; temp[40] = x[48]; temp[48] = x[56]; temp[56] = x[ 0];
    temp[ 1] = x[25]; temp[ 9] = x[33]; temp[17] = x[41]; temp[25] = x[49]; temp[33] = x[57]; temp[41] = x[ 1]; temp[49] = x[ 9]; temp[57] = x[17];
    temp[ 2] = x[42]; temp[10] = x[50]; temp[18] = x[58]; temp[26] = x[ 2]; temp[34] = x[10]; temp[42] = x[18]; temp[50] = x[26]; temp[58] = x[34];
    temp[ 3] = x[59]; temp[11] = x[ 3]; temp[19] = x[11]; temp[27] = x[19]; temp[35] = x[27]; temp[43] = x[35]; temp[51] = x[43]; temp[59] = x[51];
    temp[ 4] = x[ 4]; temp[12] = x[12]; temp[20] = x[20]; temp[28] = x[28]; temp[36] = x[36]; temp[44] = x[44]; temp[52] = x[52]; temp[60] = x[60];
    temp[ 5] = x[21]; temp[13] = x[29]; temp[21] = x[37]; temp[29] = x[45]; temp[37] = x[53]; temp[45] = x[61]; temp[53] = x[ 5]; temp[61] = x[13];
    temp[ 6] = x[38]; temp[14] = x[46]; temp[22] = x[54]; temp[30] = x[62]; temp[38] = x[ 6]; temp[46] = x[14]; temp[54] = x[22]; temp[62] = x[30];
    temp[ 7] = x[55]; temp[15] = x[63]; temp[23] = x[ 7]; temp[31] = x[15]; temp[39] = x[23]; temp[47] = x[31]; temp[55] = x[39]; temp[63] = x[47];
  }
  else
  {
    temp[ 0] = x[ 0]; temp[ 8] = x[ 8]; temp[16] = x[16]; temp[24] = x[24]; temp[32] = x[32]; temp[40] = x[40]; temp[48] = x[48]; temp[56] = x[56];
    temp[ 1] = x[ 9]; temp[ 9] = x[17]; temp[17] = x[25]; temp[25] = x[33]; temp[33] = x[41]; temp[41] = x[49]; temp[49] = x[57]; temp[57] = x[ 1];
    temp[ 2] = x[18]; temp[10] = x[26]; temp[18] = x[34]; temp[26] = x[42]; temp[34] = x[50]; temp[42] = x[58]; temp[50] = x[ 2]; temp[58] = x[10];
    temp[ 3] = x[27]; temp[11] = x[35]; temp[19] = x[43]; temp[27] = x[51]; temp[35] = x[59]; temp[43] = x[ 3]; temp[51] = x[11]; temp[59] = x[19];
    temp[ 4] = x[36]; temp[12] = x[44]; temp[20] = x[52]; temp[28] = x[60]; temp[36] = x[ 4]; temp[44] = x[12]; temp[52] = x[20]; temp[60] = x[28];
    temp[ 5] = x[45]; temp[13] = x[53]; temp[21] = x[61]; temp[29] = x[ 5]; temp[37] = x[13]; temp[45] = x[21]; temp[53] = x[29]; temp[61] = x[37];
    temp[ 6] = x[54]; temp[14] = x[62]; temp[22] = x[ 6]; temp[30] = x[14]; temp[38] = x[22]; temp[46] = x[30]; temp[54] = x[38]; temp[62] = x[46];
    temp[ 7] = x[63]; temp[15] = x[ 7]; temp[23] = x[15]; temp[31] = x[23]; temp[39] = x[31]; temp[47] = x[39]; temp[55] = x[47]; temp[63] = x[55];
  }


  for (i = 0; i < ROWS*COLS; i++)
  {
#pragma HLS UNROLL
    x[i] = temp[i];
  }
}

u8 mul2v2(u8 x)
{
#pragma HLS INLINE
  u8    x7, x6, x5, x4, x3, x2, x1, x0;
  u8    output;

  x7 = (x >> 7) & 0x1;
  x6 = (x >> 6) & 0x1;
  x5 = (x >> 5) & 0x1;
  x4 = (x >> 4) & 0x1;
  x3 = (x >> 3) & 0x1;
  x2 = (x >> 2) & 0x1;
  x1 = (x >> 1) & 0x1;
  x0 = (x >> 0) & 0x1;

  output = (x6 << 7) | \
           (x5 << 6) | \
           (x4 << 5) | \
           ((x3^x7) << 4) | \
           ((x2^x7) << 3) | \
           (x1 << 2) | \
           ((x0^x7) << 1) | \
           (x7 << 0);

  return output;
}

u8 mul3v2(u8 x)
{
#pragma HLS INLINE
  u8    x7, x6, x5, x4, x3, x2, x1, x0;
  u8    output;

  x7 = (x >> 7) & 0x1;
  x6 = (x >> 6) & 0x1;
  x5 = (x >> 5) & 0x1;
  x4 = (x >> 4) & 0x1;
  x3 = (x >> 3) & 0x1;
  x2 = (x >> 2) & 0x1;
  x1 = (x >> 1) & 0x1;
  x0 = (x >> 0) & 0x1;

  output = ((x7^x6) << 7) | \
           ((x6^x5) << 6) | \
           ((x5^x4) << 5) | \
           ((x7^x4^x3) << 4) | \
           ((x7^x3^x2) << 3) | \
           ((x2^x1) << 2) | \
           ((x7^x1^x0) << 1) | \
           ((x7^x0) << 0);

  return output;
}

u8 mul4v2(u8 x)
{
#pragma HLS INLINE
  u8    x7, x6, x5, x4, x3, x2, x1, x0;
  u8    output;

  x7 = (x >> 7) & 0x1;
  x6 = (x >> 6) & 0x1;
  x5 = (x >> 5) & 0x1;
  x4 = (x >> 4) & 0x1;
  x3 = (x >> 3) & 0x1;
  x2 = (x >> 2) & 0x1;
  x1 = (x >> 1) & 0x1;
  x0 = (x >> 0) & 0x1;

  output = ((x5) << 7) | \
           ((x4) << 6) | \
           ((x7^x3) << 5) | \
           ((x7^x6^x2) << 4) | \
           ((x6^x1) << 3) | \
           ((x7^x0) << 2) | \
           ((x7^x6) << 1) | \
           ((x6) << 0);

  return output;
}

u8 mul5v2(u8 x)
{
#pragma HLS INLINE
  u8    x7, x6, x5, x4, x3, x2, x1, x0;
  u8    output;

  x7 = (x >> 7) & 0x1;
  x6 = (x >> 6) & 0x1;
  x5 = (x >> 5) & 0x1;
  x4 = (x >> 4) & 0x1;
  x3 = (x >> 3) & 0x1;
  x2 = (x >> 2) & 0x1;
  x1 = (x >> 1) & 0x1;
  x0 = (x >> 0) & 0x1;

  output = ((x7^x5) << 7) | \
           ((x6^x4) << 6) | \
           ((x3^x5^x7) << 5) | \
           ((x7^x6^x4^x2) << 4) | \
           ((x6^x3^x1) << 3) | \
           ((x7^x2^x0) << 2) | \
           ((x7^x6^x1) << 1) | \
           ((x6^x0) << 0);

  return output;
}

u8 mul7v2(u8 x)
{
#pragma HLS INLINE
  u8    x7, x6, x5, x4, x3, x2, x1, x0;
  u8    output;

  x7 = (x >> 7) & 0x1;
  x6 = (x >> 6) & 0x1;
  x5 = (x >> 5) & 0x1;
  x4 = (x >> 4) & 0x1;
  x3 = (x >> 3) & 0x1;
  x2 = (x >> 2) & 0x1;
  x1 = (x >> 1) & 0x1;
  x0 = (x >> 0) & 0x1;

  output = ((x7^x6^x5) << 7) | \
           ((x6^x5^x4) << 6) | \
           ((x7^x5^x4^x3) << 5) | \
           ((x6^x4^x3^x2) << 4) | \
           ((x7^x6^x3^x2^x1) << 3) | \
           ((x7^x2^x1^x0) << 2) | \
           ((x6^x1^x0) << 1) | \
           ((x7^x6^x0) << 0);

  return output;
}

void MixBytes(u8 x[ROWS*COLS], u8 y[ROWS*COLS])
{
#pragma HLS INLINE
  int i, j;
  u8 temp[ROWS*COLS];

  u8 mulx2[ROWS*COLS];
  u8 mulx3[ROWS*COLS];
  u8 mulx4[ROWS*COLS];
  u8 mulx5[ROWS*COLS];
  u8 mulx7[ROWS*COLS];

  for (i = 0; i < ROWS*COLS; i++)
  {
#pragma HLS UNROLL
    mulx2[i] = mul2v2(x[i]);
    mulx3[i] = mul3v2(x[i]);
    mulx4[i] = mul4(x[i]);
    mulx5[i] = mul5v2(x[i]);
    mulx7[i] = mul7v2(x[i]);
  }

  for (i = 0; i < COLS; i++)
  {
#pragma HLS UNROLL
    for (j = 0; j < ROWS; j++)
    {
#pragma HLS UNROLL
      temp[i*8+j] =
        mulx2[i*8+((j+0)%ROWS)]^
        mulx2[i*8+((j+1)%ROWS)]^
        mulx3[i*8+((j+2)%ROWS)]^
        mulx4[i*8+((j+3)%ROWS)]^
        mulx5[i*8+((j+4)%ROWS)]^
        mulx3[i*8+((j+5)%ROWS)]^
        mulx5[i*8+((j+6)%ROWS)]^
        mulx7[i*8+((j+7)%ROWS)];
    }
  }

  for (i = 0; i < ROWS*COLS; i++)
  {
#pragma HLS UNROLL
    y[i] = temp[i];
  }
}

void groestl(u8 data[ROWS*COLS], u8 output[ROWS*COLS/2], uint1 last)
{
#pragma HLS INTERFACE ap_hs port=output

  int i,j;
  u8 state_reg1[ROWS*COLS] = {
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0};    
  u8 state_reg2[ROWS*COLS] = {
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0};
  u8 state_tmp1[ROWS*COLS];
  u8 state_tmp2[ROWS*COLS];
  u8 m[ROWS*COLS];
  u8 round;
  u8 total_round;
  u8 actual_round;
  uint1 is_q;
  static u8 hash[ROWS*COLS] = {
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 1, 0};
  u8 new_hash[ROWS*COLS];

#pragma HLS ARRAY_RESHAPE variable=data complete dim=1
#pragma HLS ARRAY_RESHAPE variable=output complete dim=1
#pragma HLS ARRAY_RESHAPE variable=state_reg1 complete dim=1
#pragma HLS ARRAY_RESHAPE variable=state_reg2 complete dim=1
#pragma HLS ARRAY_RESHAPE variable=m complete dim=1
#pragma HLS ARRAY_RESHAPE variable=hash complete dim=1


  /* Initialization */
  // Copy data to temporary var
  for (i = 0; i < ROWS*COLS; i++)
  {
#pragma HLS UNROLL
    m[i] = data[i];
  }

#if DEBUG
    printf("Start processing\n");
    printf("\tInput (data):\n");
    printState(data, 64);
    printf("\n");

    printf("\tInput (m):\n");
    printState(m, 64);
    printf("\tHash state:\n");
    printState(hash, 32);
#endif

  // H ^ M
  for (i = 0; i < ROWS*COLS; i++)
  {
#pragma HLS UNROLL
    state_reg1[i] = hash[i] ^ m[i];
  }

  if (last == 1)
    total_round = NB_ROUNDS*2-1;
  else
    total_round = NB_ROUNDS;

  /* Main Loop */
  for (round = 0; round < total_round; round++)
  {
#if DEBUG
    printf("Beginning of Round %d\n", round);
    printf("    State Reg1:\n");
    printState(state_reg1, 64);
#endif
    if (round < NB_ROUNDS)
      actual_round = round >> 1;
    else
      actual_round = (round-NB_ROUNDS) >> 1;

    is_q = round % 2;
    /* Real hardware uint1 truncates ~ to 1 bit; our portable uint1 stand-in
       (see ap_cint.h) is wider, so mask explicitly to keep the 0/1 toggle. */
    if (round >= NB_ROUNDS) is_q = (~is_q) & 0x1;

    // P
    AddRoundConstant(state_reg1, actual_round, is_q);
#if DEBUG_ROUND
  printf("  After AddConstant:\n");
  printState(state_reg1, 64);
#endif
    SubBytes(state_reg1, state_tmp1);
#if DEBUG_ROUND
  printf("  After SubBytes:\n");
  printState(state_tmp1, 64);
    printf("    State Reg2:\n");
    printState(state_reg2, 64);
#endif
    // P
    ShiftBytes(state_reg2, is_q);
#if DEBUG_ROUND
    printf("  After ShiftBytes:\n");
    printState(state_reg2, 64);
#endif
    MixBytes(state_reg2, state_tmp2);
#if DEBUG_ROUND
    printf("  After MixBytes:\n");
    printState(state_tmp2, 64);
#endif


    for (i = 0; i < ROWS*COLS; i++)
    {
#pragma HLS UNROLL
      new_hash[i] = state_tmp2[i] ^ hash[i];
    }

    // Copy state_tmp to reg2
    for (i = 0; i < ROWS*COLS; i++)
    {
#pragma HLS UNROLL
      state_reg2[i] = state_tmp1[i];
    }

    // State_reg1 new data
    if (round == 0)
      for (i = 0; i < ROWS*COLS; i++)
      {
#pragma HLS UNROLL
        state_reg1[i] = m[i];
      }
    else if (round == NB_ROUNDS-1)
      for (i = 0; i < ROWS*COLS; i++)
      {
#pragma HLS UNROLL
        state_reg1[i] = new_hash[i];
      }
    else
      for (i = 0; i < ROWS*COLS; i++)
      {
#pragma HLS UNROLL
        state_reg1[i] = state_tmp2[i];
      }

    // Store new hash data
    if ((round == NB_ROUNDS-2) || (round == NB_ROUNDS-1))
      for (i = 0; i < ROWS*COLS; i++)
      {
  #pragma HLS UNROLL
        hash[i] = new_hash[i];
      }
    else if (round == NB_ROUNDS*2-2)
    {
      // Output
      for (i = 0; i < ROWS*COLS/2; i++)
      {
  #pragma HLS UNROLL
        output[i] = new_hash[ROWS*COLS/2+i];
      }

      // Reset IV
      hash[ 0] = 0; hash[ 1] = 0; hash[ 2] = 0; hash[ 3] = 0;
      hash[ 4] = 0; hash[ 5] = 0; hash[ 6] = 0; hash[ 7] = 0;
      hash[ 8] = 0; hash[ 9] = 0; hash[10] = 0; hash[11] = 0;
      hash[12] = 0; hash[13] = 0; hash[14] = 0; hash[15] = 0;
      hash[16] = 0; hash[17] = 0; hash[18] = 0; hash[19] = 0;
      hash[20] = 0; hash[21] = 0; hash[22] = 0; hash[23] = 0;
      hash[24] = 0; hash[25] = 0; hash[26] = 0; hash[27] = 0;
      hash[28] = 0; hash[29] = 0; hash[30] = 0; hash[31] = 0;
      hash[32] = 0; hash[33] = 0; hash[34] = 0; hash[35] = 0;
      hash[36] = 0; hash[37] = 0; hash[38] = 0; hash[39] = 0;
      hash[40] = 0; hash[41] = 0; hash[42] = 0; hash[43] = 0;
      hash[44] = 0; hash[45] = 0; hash[46] = 0; hash[47] = 0;
      hash[48] = 0; hash[49] = 0; hash[50] = 0; hash[51] = 0;
      hash[52] = 0; hash[53] = 0; hash[54] = 0; hash[55] = 0;
      hash[56] = 0; hash[57] = 0; hash[58] = 0; hash[59] = 0;
      hash[60] = 0; hash[61] = 0; hash[62] = 1; hash[63] = 0;
    }
  }
//
//#if DEBUG
//      printf("Hash value:\n");
//      printState(new_hash, 64);
//#endif
//
//  /* Last block */
//  if (last == 1)
//  {
//
//    // Output
//    for (i = 0; i < ROWS*COLS/2; i++)
//    {
//#pragma HLS UNROLL
//      output[i] = new_hash[ROWS*COLS/2+i];
//    }
//
//    // Reset IV
//    hash[ 0] = 0; hash[ 1] = 0; hash[ 2] = 0; hash[ 3] = 0;
//    hash[ 4] = 0; hash[ 5] = 0; hash[ 6] = 0; hash[ 7] = 0;
//    hash[ 8] = 0; hash[ 9] = 0; hash[10] = 0; hash[11] = 0;
//    hash[12] = 0; hash[13] = 0; hash[14] = 0; hash[15] = 0;
//    hash[16] = 0; hash[17] = 0; hash[18] = 0; hash[19] = 0;
//    hash[20] = 0; hash[21] = 0; hash[22] = 0; hash[23] = 0;
//    hash[24] = 0; hash[25] = 0; hash[26] = 0; hash[27] = 0;
//    hash[28] = 0; hash[29] = 0; hash[30] = 0; hash[31] = 0;
//    hash[32] = 0; hash[33] = 0; hash[34] = 0; hash[35] = 0;
//    hash[36] = 0; hash[37] = 0; hash[38] = 0; hash[39] = 0;
//    hash[40] = 0; hash[41] = 0; hash[42] = 0; hash[43] = 0;
//    hash[44] = 0; hash[45] = 0; hash[46] = 0; hash[47] = 0;
//    hash[48] = 0; hash[49] = 0; hash[50] = 0; hash[51] = 0;
//    hash[52] = 0; hash[53] = 0; hash[54] = 0; hash[55] = 0;
//    hash[56] = 0; hash[57] = 0; hash[58] = 0; hash[59] = 0;
//    hash[60] = 0; hash[61] = 0; hash[62] = 1; hash[63] = 0;
//  }
//  else
//  {
//    for (i = 0; i < ROWS*COLS; i++)
//    {
//#pragma HLS UNROLL
//      hash[i] = new_hash[i];
//    }
//  }
}
