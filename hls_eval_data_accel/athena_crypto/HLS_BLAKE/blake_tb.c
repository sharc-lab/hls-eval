/* *
 * @file       blake_tb.c
 * @brief      Testbench used for HLS-based BLAKE in software
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

#define TEST1 0

typedef unsigned int u32;
typedef unsigned char u8;
void BLAKE32(u32 *, u32 *, u32 *, u8 , u32);

void printData(u32 *data, u32 size)
{
  int i;
  for (i=0; i<size; i++)
  {
    printf("%08X ", data[i]);
    if ((i+1)%8 == 0) printf("\n");
  }
  printf("\n");
}

int testBlake() {
  int i;
  int pass = 1;
  u32 size;
#if TEST1
  u32 input[16] = {
      0x00800000, 0x00000000,
      0x00000000, 0x00000000,
      0x00000000, 0x00000000,
      0x00000000, 0x00000000,
      0x00000000, 0x00000000,
      0x00000000, 0x00000000,
      0x00000000, 0x00000001,
      0x00000000, 0x00000008
  };
  u32 exp[16]={
      0x0CE8D4EF, 0x4DD7CD8D, 0x62DFDED9, 0xD4EDB0A7,
      0x74AE6A41, 0x929A74DA, 0x23109E8F, 0x11139C87
  };
#else
  u32 input[16] = {
       0x0000000, 0x00000000,
       0x00000000, 0x00000000,
       0x00000000, 0x00000000,
       0x00000000, 0x00000000,
       0x00000000, 0x00000000,
       0x00000000, 0x00000000,
       0x00000000, 0x00000000,
       0x00000000, 0x00000000
   };
  u32 input2[16] = {
        0x00000000, 0x00000000,
        0x80000000, 0x00000000,
        0x00000000, 0x00000000,
        0x00000000, 0x00000000,
        0x00000000, 0x00000000,
        0x00000000, 0x00000000,
        0x00000000, 0x00000001,
        0x00000000, 0x00000240
    };
  u32 exp[16]={
      0xD419BAD3, 0x2D504FB7, 0xD44D460C, 0x42C5593F,
      0xE544FA4C, 0x135DEC31, 0xE21BD9AB, 0xDCC22D41
    };
#endif
  u32 output[16];



  for (i=0; i<16; i++)
    output[i] = 0;

  printf("Pre-hash:\n");
  printData(output, 8);
#if TEST1
  BLAKE32(input, input, output, 1, 8);
#else
  BLAKE32(input, input, output, 0, 512);
  BLAKE32(input2, input2, output, 1, 64);
#endif
  printf("Post-hash:\n");
  printData(output, 8);
  printf("Expect:\n");
  printData(exp, 8);

  /* Check result */
  for(i=0; i<8; i++)
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
  return testBlake() ? 0 : 1;
}
