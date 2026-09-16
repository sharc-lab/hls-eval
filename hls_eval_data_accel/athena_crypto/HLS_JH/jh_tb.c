/* *
 * @file       blake_tb.c
 * @brief      Testbench used for HLS-based JH in software
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

#define TEST1 1

void jh(uint8 *, uint8 *, uint1, uint1);

void printData(uint8 *data, int size)
{
  int i;
  for (i=0; i<size; i++)
  {
    printf("%02X", data[i]);
    if ((i+1)%4 == 0) printf(" ");
    if ((i+1)%32 == 0) printf("\n");
  }
  printf("\n");
}

int testJH() {
  int i, j;
  int pass = 1;
  uint8 input1[64];
  uint8 input2[64];
  uint8 output[32];

#if TEST1
  input1[0] = 0xCC;
  input1[1] = 0x80;
  for (i=2; i<64; i++) input1[i] = 0;
  for (i=0; i<63; i++) input2[i] = 0;
  input2[63] = 0x08;

  uint8 exp[32]={
      0x7B, 0x11, 0x91, 0xF1, 0x3A, 0x26, 0x67, 0x83,
      0x01, 0x42, 0x54, 0x1B, 0xFC, 0x59, 0x18, 0x54,
      0x3D, 0x2A, 0x43, 0x4C, 0x76, 0x92, 0xE7, 0x0C,
      0x3E, 0x5E, 0x9B, 0xBD, 0xDD, 0xB7, 0xF5, 0x81
  };

#else
  UINT64 input[17] = {
    0x157D5B7E4507F66D, 0x9A267476D33831E7, 0xBB768D4D04CC3438, 0xDA12F9010263EA5F,
    0xCAFBDE2579DB2F6B, 0x58F911D593D5F79F, 0xB05FE3596E3FA80F, 0xF2F761D1B0E57080,
    0x055C118C53E53CDB, 0x63055261D7C9B2B3, 0x9BD90ACC32520CBB, 0xDBDA2C4FD8856DBC,
    0xEE173132A2679198, 0xDAF83007A9B5C515, 0x11AE49766C792A29, 0x520388444EBEFE28
  };
  UINT64 input2[17] = {
    0xBA73A9479EE00C63, 0x0100000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000080
  };
  UINT64 exp[4]={
    0x4CE7C2B935F21FC3, 0x4C5E56D940A555C5, 0x93872AEC2F896DE4, 0xE68F2A017060F535
  };

  for (i=0; i<17; i++)
  {
     tmp = 0;
     for (j=0; j<8; j++)
       tmp ^= ((input[i] >> j*8) & 0xFF) << ((7-j)*8);
     input[i] = tmp;
     tmp = 0;
     for (j=0; j<8; j++)
       tmp ^= ((input2[i] >> j*8) & 0xFF) << ((7-j)*8);
     input2[i] = tmp;
  }
#endif

  for (i=0; i<32; i++) output[i] = 0;

  printf("Input data:\n");
  printData(input1, 64);
  printData(input2, 64);

#if TEST1
  jh(input1, output, 1, 0);
  jh(input2, output, 0, 1);
#else
  JH(input, output, 0);
  JH(input2, output, 1);
#endif


  printf("Post-hash:\n");
  printData(output, 32);
  printf("Expect:\n");
  printData(exp, 32);

  /* Check result */
  for(i=0; i<32; i++)
    if (exp[i] != output[i]) {printf("Test fail at word %d\n", i); pass = 0;}
  if (pass == 1)
#if TEST1
    printf("Hooray! One block test passed\n");
#else
    printf("Hooray! Two block test passed\n");
#endif



  return pass;
}

int main() {
  return testJH() ? 0 : 1;
}
