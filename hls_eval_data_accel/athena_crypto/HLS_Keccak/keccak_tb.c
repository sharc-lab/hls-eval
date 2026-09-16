/* *
 * @file       keccak_tb.c
 * @brief      Testbench used for HLS-based Keccak in software
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

typedef uint64 UINT64;
void keccak(UINT64 *, UINT64 *, uint1);

void printData(UINT64 *data, int size)
{
  int i;
  for (i=0; i<size; i++)
  {
    printf("%016llX ", data[i]);
    if ((i+1)%5 == 0) printf("\n");
  }
  printf("\n");
}

int testKeccak() {
  int i, j;
  int pass = 1;
  UINT64 tmp;
#if TEST1
  UINT64 input[17] = {
    0xCC01000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000080
  };
  UINT64 exp[4]={
      0xEEAD6DBFC7340A56, 0xCAEDC044696A1688, 
      0x70549A6A7F6F5696, 0x1E84A54BD9970B8A
  };

  for (i=0; i<17; i++)
  {
     tmp = 0;
     for (j=0; j<8; j++)
       tmp ^= ((input[i] >> j*8) & 0xFF) << ((7-j)*8);
     input[i] = tmp;
  }
#else
  UINT64 input[17] = {
    0x157D5B7E4507F66D, 0x9A267476D33831E7, 0xBB768D4D04CC3438, 0xDA12F9010263EA5F,
    0xCAFBDE2579DB2F6B, 0x58F911D593D5F79F, 0xB05FE3596E3FA80F, 0xF2F761D1B0E57080,
    0x055C118C53E53CDB, 0x63055261D7C9B2B3, 0x9BD90ACC32520CBB, 0xDBDA2C4FD8856DBC,
    0xEE173132A2679198, 0xDAF83007A9B5C515, 0x11AE49766C792A29, 0x520388444EBEFE28,
    0x256FB33D4260439C
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
  UINT64 output[4];

  for (i=0; i<4; i++)
    output[i] = 0;

  printf("Input data:\n");
  printData(input, 17);

#if TEST1
  keccak(input, output, 1);
#else
  keccak(input, output, 0);
  keccak(input2, output, 1);
#endif


  for (i=0; i<4; i++)
    {
       tmp = 0;
       for (j=0; j<8; j++)
         tmp ^= ((output[i] >> j*8) & 0xFF) << ((7-j)*8);
       output[i] = tmp;
    }

  printf("Post-hash:\n");
  printData(output, 4);
  printf("Expect:\n");
  printData(exp, 4);

  /* Check result */
  for(i=0; i<4; i++)
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
  return testKeccak() ? 0 : 1;
}
