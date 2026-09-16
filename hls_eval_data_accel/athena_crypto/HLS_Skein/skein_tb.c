/* *
 * @file       skein_tb.c
 * @brief      Testbench used for HLS-based Skein in software
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

#define TEST1 0

typedef uint64 UINT64;
void skein(UINT64 *, UINT64 *, uint1, uint1, uint32 size);

void printData(UINT64 *data, int size)
{
  int i;
  for (i=0; i<size; i++)
  {
    printf("%016llX ", data[size-1-i]);
    if ((i+1)%4 == 0) printf("\n");
  }
  printf("\n");
}

int testSkein() {
  int i, j;
  int pass = 1;
  UINT64 tmp;
  UINT64 output[4];

#if TEST1
  UINT64 input[8] = {
    0xCC00000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000,
    0x0000000000000000, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000
  };
  UINT64 exp[4]={
    0xA018268ED814E0AD, 0x0F2D0304E8FE3F41,
    0x18FCEFC07454D071, 0x23CC2C3E40E06A4F
  };

  for (i=0; i<8; i++)
  {
     tmp = 0;
     for (j=0; j<8; j++)
       tmp ^= ((input[i] >> j*8) & 0xFF) << ((7-j)*8);
     input[i] = tmp;
  }
#else
  UINT64 input[8] = {
      0xF13C972C52CB3CC4, 0xA4DF28C97F2DF11C, 0xE089B815466BE888, 0x63243EB318C2ADB1,
      0xA417CB1041308598, 0x541720197B9B1CB5, 0xBA2318BD5574D1DF, 0x2174AF14884149BA

  };
  UINT64 input2[8] = {
      0x9B2F446D609DF240, 0xCE335599957B8EC8, 0x0876D9A085AE0849, 0x07BC5961B20BF5F6,
      0xCA58D5DAB38ADB00, 0x0000000000000000, 0x0000000000000000, 0x0000000000000000
  };
  UINT64 exp[4]={
    0xD8A7E38369BE5155, 0x5C48D30178A90C96, 0x1C429825C0335EE7, 0x7D91611C7DD7F99A    
  };

  for (i=0; i<8; i++)
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

  for (i=0; i<4; i++)
    output[i] = 0;

  printf("Input data:\n");
  printData(input, 8);

  printf("Pre-hash data:\n");
  printData(output, 4);

#if TEST1
  skein(input, output, 1, 1, 1);
#else
  skein(input, output, 1, 0, 64);
  skein(input2, output, 0, 1, 39);
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
  return testSkein() ? 0 : 1;
}
