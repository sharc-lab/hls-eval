/* *
 * @file       blake_hls.c
 * @brief      HLS-based BLAKE implementation in C
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

#define DEBUG 0
#define DEBUG_ROUND 0
#define DEBUG_PERMUTE 0


#define NB_ROUNDS32 14


typedef unsigned int u32;
typedef unsigned char u8;

/*
  constants for BLAKE-32 and BLAKE-28
*/

static void printState(u32 state[16], u32 size)
{
  int i;
  for (i=0; i<size; i++)
  {
    printf("%08X ", state[i]);
    if ((i==7)||(i==15)) printf("\n");
  }
}

void permute(u32 m_first[16], u32 m[16], u32 c[16], u32 mxc[8], uint5 round)
{
#pragma HLS INLINE
  static const unsigned char sigma[20][8] = {
    {  0,  1,  2,  3,  4,  5,  6,  7}, { 8,  9, 10, 11, 12, 13, 14, 15 } ,
    { 14, 10,  4,  8,  9, 15, 13,  6}, { 1, 12,  0,  2, 11,  7,  5,  3 } ,
    { 11,  8, 12,  0,  5,  2, 15, 13}, {10, 14,  3,  6,  7,  1,  9,  4 } ,
    {  7,  9,  3,  1, 13, 12, 11, 14}, { 2,  6,  5, 10,  4,  0, 15,  8 } ,
    {  9,  0,  5,  7,  2,  4, 10, 15}, {14,  1, 11, 12,  6,  8,  3, 13 } ,
    {  2, 12,  6, 10,  0, 11,  8,  3}, { 4, 13,  7,  5, 15, 14,  1,  9 } ,
    { 12,  5,  1, 15, 14, 13,  4, 10}, { 0,  7,  6,  3,  9,  2,  8, 11 } ,
    { 13, 11,  7, 14, 12,  1,  3,  9}, { 5,  0, 15,  4,  8,  6,  2, 10 } ,
    {  6, 15, 14,  9, 11,  3,  0,  8}, {12,  2, 13,  7,  1,  4, 10,  5 } ,
    { 10,  2,  8,  4,  7,  6,  1,  5}, {15, 11,  9, 14,  3, 12, 13 , 0 }
  };
  int i;
  
  u32 c00[8], c01[8], c02[8], c03[8];
  u32 c04[8], c05[8], c06[8], c07[8];
  u32 c08[8], c09[8], c10[8], c11[8];
  u32 c12[8], c13[8], c14[8], c15[8];
  u32 c16[8], c17[8], c18[8], c19[8];

  u32 m00_first[8];
  u32 m00[8], m01[8], m02[8], m03[8];
  u32 m04[8], m05[8], m06[8], m07[8];
  u32 m08[8], m09[8], m10[8], m11[8];
  u32 m12[8], m13[8], m14[8], m15[8];
  u32 m16[8], m17[8], m18[8], m19[8];

  u32 msel[8], csel[8];
  
#pragma HLS ARRAY_RESHAPE variable=msel complete dim=1
#pragma HLS ARRAY_RESHAPE variable=csel complete dim=1

  for (i=0; i<8; i++)
  {
#pragma HLS UNROLL
    m00_first[i] = m_first[sigma[0][i]];
    m00[i] = m[sigma[0][i]]; c00[i] = c[sigma[0][i]];
    m01[i] = m[sigma[1][i]]; c01[i] = c[sigma[1][i]];
    m02[i] = m[sigma[2][i]]; c02[i] = c[sigma[2][i]];
    m03[i] = m[sigma[3][i]]; c03[i] = c[sigma[3][i]];
    m04[i] = m[sigma[4][i]]; c04[i] = c[sigma[4][i]];
    m05[i] = m[sigma[5][i]]; c05[i] = c[sigma[5][i]];
    m06[i] = m[sigma[6][i]]; c06[i] = c[sigma[6][i]];
    m07[i] = m[sigma[7][i]]; c07[i] = c[sigma[7][i]];
    m08[i] = m[sigma[8][i]]; c08[i] = c[sigma[8][i]];
    m09[i] = m[sigma[9][i]]; c09[i] = c[sigma[9][i]];
    m10[i] = m[sigma[10][i]]; c10[i] = c[sigma[10][i]];
    m11[i] = m[sigma[11][i]]; c11[i] = c[sigma[11][i]];
    m12[i] = m[sigma[12][i]]; c12[i] = c[sigma[12][i]];
    m13[i] = m[sigma[13][i]]; c13[i] = c[sigma[13][i]];
    m14[i] = m[sigma[14][i]]; c14[i] = c[sigma[14][i]];
    m15[i] = m[sigma[15][i]]; c15[i] = c[sigma[15][i]];
    m16[i] = m[sigma[16][i]]; c16[i] = c[sigma[16][i]];
    m17[i] = m[sigma[17][i]]; c17[i] = c[sigma[17][i]];
    m18[i] = m[sigma[18][i]]; c18[i] = c[sigma[18][i]];
    m19[i] = m[sigma[19][i]]; c19[i] = c[sigma[19][i]];
  }
  
  if      (round ==  0) {memcpy(msel, m00_first, 8*sizeof(unsigned int)); memcpy(csel, c00, 8*sizeof(unsigned int)); }
  else if (round ==  1 || round == 21) {memcpy(msel, m01, 8*sizeof(unsigned int)); memcpy(csel, c01, 8*sizeof(unsigned int)); }
  else if (round ==  2 || round == 22) {memcpy(msel, m02, 8*sizeof(unsigned int)); memcpy(csel, c02, 8*sizeof(unsigned int)); }
  else if (round ==  3 || round == 23) {memcpy(msel, m03, 8*sizeof(unsigned int)); memcpy(csel, c03, 8*sizeof(unsigned int)); }
  else if (round ==  4 || round == 24) {memcpy(msel, m04, 8*sizeof(unsigned int)); memcpy(csel, c04, 8*sizeof(unsigned int)); }
  else if (round ==  5 || round == 25) {memcpy(msel, m05, 8*sizeof(unsigned int)); memcpy(csel, c05, 8*sizeof(unsigned int)); }
  else if (round ==  6 || round == 26) {memcpy(msel, m06, 8*sizeof(unsigned int)); memcpy(csel, c06, 8*sizeof(unsigned int)); }
  else if (round ==  7 || round == 27) {memcpy(msel, m07, 8*sizeof(unsigned int)); memcpy(csel, c07, 8*sizeof(unsigned int)); }
  else if (round ==  8 || round == 28) {memcpy(msel, m08, 8*sizeof(unsigned int)); memcpy(csel, c08, 8*sizeof(unsigned int)); }
  else if (round ==  9 || round == 29) {memcpy(msel, m09, 8*sizeof(unsigned int)); memcpy(csel, c09, 8*sizeof(unsigned int)); }
  else if (round == 10 || round == 30) {memcpy(msel, m10, 8*sizeof(unsigned int)); memcpy(csel, c10, 8*sizeof(unsigned int)); }
  else if (round == 11 || round == 31) {memcpy(msel, m11, 8*sizeof(unsigned int)); memcpy(csel, c11, 8*sizeof(unsigned int)); }
  else if (round == 12) {memcpy(msel, m12, 8*sizeof(unsigned int)); memcpy(csel, c12, 8*sizeof(unsigned int)); }
  else if (round == 13) {memcpy(msel, m13, 8*sizeof(unsigned int)); memcpy(csel, c13, 8*sizeof(unsigned int)); }
  else if (round == 14) {memcpy(msel, m14, 8*sizeof(unsigned int)); memcpy(csel, c14, 8*sizeof(unsigned int)); }
  else if (round == 15) {memcpy(msel, m15, 8*sizeof(unsigned int)); memcpy(csel, c15, 8*sizeof(unsigned int)); }
  else if (round == 16) {memcpy(msel, m16, 8*sizeof(unsigned int)); memcpy(csel, c16, 8*sizeof(unsigned int)); }
  else if (round == 17) {memcpy(msel, m17, 8*sizeof(unsigned int)); memcpy(csel, c17, 8*sizeof(unsigned int)); }
  else if (round == 18) {memcpy(msel, m18, 8*sizeof(unsigned int)); memcpy(csel, c18, 8*sizeof(unsigned int)); }
  else if (round == 19) {memcpy(msel, m19, 8*sizeof(unsigned int)); memcpy(csel, c19, 8*sizeof(unsigned int)); }
  else                  {memcpy(msel, m00, 8*sizeof(unsigned int)); memcpy(csel, c00, 8*sizeof(unsigned int)); }

  for (i=0; i<4; i++)
  {
#pragma HLS UNROLL
    mxc[2*i+0] = msel[2*i] ^ csel[2*i+1];
    mxc[2*i+1] = msel[2*i+1] ^ csel[2*i];
//    mxc[2*i+0] = msel[2*i];
//    mxc[2*i+1] = msel[2*i+1];
  }
}

void BLAKE32(u32 data[16], u32 data_reg[16], u32 output[8], uint1 last, u32 size)
{
#pragma HLS INTERFACE ap_hs port=output

  u32 v[16];
  u32 tmp[16];
  u32 mxc[8];
  u32 new_hash[8];

  uint5  round = 0;
  u8  i, j;


  u32 c32[16] = {
      0x243F6A88, 0x85A308D3,
      0x13198A2E, 0x03707344,
      0xA4093822, 0x299F31D0,
      0x082EFA98, 0xEC4E6C89,
      0x452821E6, 0x38D01377,
      0xBE5466CF, 0x34E90C6C,
      0xC0AC29B7, 0xC97C50DD,
      0x3F84D5B5, 0xB5470917
  };
  static u32 hash[8] = {
    0x6A09E667, 0xBB67AE85,
    0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C,
    0x1F83D9AB, 0x5BE0CD19
  };

  static u32 t32[2] = {0, 0};


#pragma HLS ARRAY_RESHAPE variable=data complete dim=1
#pragma HLS ARRAY_RESHAPE variable=data_reg complete dim=1
#pragma HLS ARRAY_RESHAPE variable=output complete dim=1
#pragma HLS ARRAY_RESHAPE variable=v complete dim=1
#pragma HLS ARRAY_RESHAPE variable=tmp complete dim=1
#pragma HLS ARRAY_RESHAPE variable=mxc complete dim=1
#pragma HLS ARRAY_RESHAPE variable=hash complete dim=1
#pragma HLS ARRAY_RESHAPE variable=t32 complete dim=1
#pragma HLS ARRAY_RESHAPE variable=c32 complete dim=1


#define ROT32(x,n) (((x)<<(32-n))|( (x)>>(n)))
#define ADD32(x,y)   ((u32)((x) + (y)))
#define XOR32(x,y)    ((u32)((x) ^ (y)))

#define G32(a,b,c,d,i)\
  do { \
    v[a] = ADD32(v[a],v[b])+mxc[2*i];\
    v[d] = ROT32(XOR32(v[d],v[a]),16);\
    v[c] = ADD32(v[c],v[d]);\
    v[b] = ROT32(XOR32(v[b],v[c]),12);\
    v[a] = ADD32(v[a],v[b])+mxc[2*i+1];\
    v[d] = ROT32(XOR32(v[d],v[a]), 8);\
    v[c] = ADD32(v[c],v[d]);\
    v[b] = ROT32(XOR32(v[b],v[c]), 7);\
  } while (0)

  /* initialization */
  if (size > 0)
  {
    t32[0] += size;
    if (t32[0] == 0)
      t32[1]++;
  }
  else
  {
    t32[0] = 0;
    t32[1] = 0;
  }

  v[ 0] = hash[0];
  v[ 1] = hash[1];
  v[ 2] = hash[2];
  v[ 3] = hash[3];
  v[ 4] = hash[4];
  v[ 5] = hash[5];
  v[ 6] = hash[6];
  v[ 7] = hash[7];
  v[ 8] = c32[0];
  v[ 9] = c32[1];
  v[10] = c32[2];
  v[11] = c32[3];
  v[12] = c32[4] ^ t32[0];
  v[13] = c32[5] ^ t32[0];
  v[14] = c32[6] ^ t32[1];
  v[15] = c32[7] ^ t32[1];

#if DEBUG || DEBUG_ROUND
  printf("Initial state of v:\n");
  printState(v,16);

  printf("Counter:\n");
  printf("%08X %08X\n",t32[0],t32[1]);
#endif

  permute(data, data_reg, c32, mxc, 0);

  /*  do 14 rounds */
  for(round=0; round<NB_ROUNDS32*2; ++round)
  {
#if DEBUG
    printf("Round %d \n", round+1);
    printf("Precompute MxC:\n");
    printState(mxc,8);
#endif

    /* column step */
    G32( 0, 4, 8,12, 0);
    G32( 1, 5, 9,13, 1);
    G32( 2, 6,10,14, 2);
    G32( 3, 7,11,15, 3);

#if DEBUG_PERMUTE
    printf("Pre-permuted state:\n");
    printState(v,16);
#endif

    // Permutation
    if (round % 2 == 0)
    { // Forward permutation
      for(i=0; i<4; i++)
      {
#pragma HLS UNROLL
        for(j=0; j<4; j++)
        {
#pragma HLS UNROLL
          tmp[i*4+j] = v[((j+i)%4)+i*4];
        }
      }
    }
    else
    { // Backward permutation
      for(i=0; i<4; i++)
      {
#pragma HLS UNROLL
        for(j=0; j<4; j++)
        {
#pragma HLS UNROLL
          tmp[i*4+j] = v[((j+4-i)%4)+i*4];
        }
      }
    }

    for (i=0; i<16; i++)
    {
#pragma HLS UNROLL
      v[i] = tmp[i];
    }

#if DEBUG_ROUND
    printf("State v after round %d:\n", round+1);
    printState(v,16);
#endif
    permute(data, data_reg, c32, mxc, round+1);
  }

  /* finalization */
  new_hash[0] = v[ 0]^v[ 8]^hash[0];
  new_hash[1] = v[ 1]^v[ 9]^hash[1];
  new_hash[2] = v[ 2]^v[10]^hash[2];
  new_hash[3] = v[ 3]^v[11]^hash[3];
  new_hash[4] = v[ 4]^v[12]^hash[4];
  new_hash[5] = v[ 5]^v[13]^hash[5];
  new_hash[6] = v[ 6]^v[14]^hash[6];
  new_hash[7] = v[ 7]^v[15]^hash[7];

  /* Output */
  if (last == 1)
  {
    hash[0] = 0x6A09E667;
    hash[1] = 0xBB67AE85;
    hash[2] = 0x3C6EF372;
    hash[3] = 0xA54FF53A;
    hash[4] = 0x510E527F;
    hash[5] = 0x9B05688C;
    hash[6] = 0x1F83D9AB;
    hash[7] = 0x5BE0CD19;
    t32[0] = 0;
    t32[1] = 0;
    for (i = 0; i < 8; i++)
    {
#pragma HLS UNROLL
      output[i] = new_hash[i];
    }
  }
  else
    for (i = 0; i < 8; i++)
    {
#pragma HLS UNROLL
      hash[i] = new_hash[i];
    }
}
