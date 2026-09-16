/* *
 * @file       jh_hls.c
 * @brief      HLS-based JH implementation in C
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
#include "jh_hls.h"
#include "ap_cint.h"

#define DEBUG 0
#define DEBUG_ROUND 0
#define NB_ROUNDS 42

typedef uint64 UINT64;

#define index(x, y) (((x)%5)+5*((y)%5))
#define ROL64(a, offset) ((offset != 0) ? ((((UINT64)a) << offset) ^ (((UINT64)a) >> (64-offset))) : a)

void printHash(uint8 hash[128])
{
  int x;
  printf("  ");
  for (x = 0; x < 128; x++)
  {
    printf("%02X", hash[x]);
    if ((x+1)%4 == 0) printf(" ");
    if ((x+1)%32 == 0) printf("\n  ");
  }
  printf("\n");
}

void printState(uint4 state[256])
{
  int x;
  printf("  ");
  for (x = 0; x < 256; x++)
  {
    printf("%01X", state[x]);
    if ((x+1)%8 == 0) printf(" ");
    if ((x+1)%32 == 0) printf("\n  ");
  }
  printf("\n");
}
/*initial group at the begining of E_8: group the bits of H into 4-bit elements of A.
  After the grouping, the i-th, (i+256)-th, (i+512)-th, (i+768)-th bits of state->H
  become the i-th 4-bit element of state->A
*/
void E8_initialgroup(uint8 H[128], uint4 A[256]) {
  unsigned int i;
  unsigned char t0,t1,t2,t3;
  unsigned char tem[256];

#pragma HLS ARRAY_RESHAPE variable=H complete dim=1
#pragma HLS ARRAY_RESHAPE variable=A complete dim=1
#pragma HLS ARRAY_RESHAPE variable=tem complete dim=1


  /*t0 is the i-th bit of H, i = 0, 1, 2, 3, ... , 127*/
  /*t1 is the (i+256)-th bit of H*/
  /*t2 is the (i+512)-th bit of H*/
  /*t3 is the (i+768)-th bit of H*/
  for (i = 0; i < 256; i++)
  {
#pragma HLS UNROLL
    t0 = (H[i>>3] >> (7 - (i & 7)) ) & 1;
    t1 = (H[(i+256)>>3] >> (7 - (i & 7)) ) & 1;
    t2 = (H[(i+ 512 )>>3] >> (7 - (i & 7)) ) & 1;
    t3 = (H[(i+ 768 )>>3] >> (7 - (i & 7)) ) & 1;
    tem[i] = (t0 << 3) | (t1 << 2) | (t2 << 1) | (t3 << 0);
  }
  /*padding the odd-th elements and even-th elements separately*/
  for (i = 0; i < 128; i++)
  {
#pragma HLS UNROLL
    A[i << 1]     = tem[i];
    A[(i << 1)+1] = tem[i+128];
  }
}

/*de-group at the end of E_8:  it is the inverse of E8_initialgroup
  The 256 4-bit elements in state->A are degouped into the 1024-bit state->H
*/
void E8_finaldegroup(uint4 A[256], uint8 H[128])
{
  unsigned int i;
  unsigned char t0,t1,t2,t3;
  unsigned char tem[256];

#pragma HLS ARRAY_RESHAPE variable=H complete dim=1
#pragma HLS ARRAY_RESHAPE variable=A complete dim=1
#pragma HLS ARRAY_RESHAPE variable=tem complete dim=1

  for (i = 0; i < 128; i++)
  {
#pragma HLS UNROLL
    tem[i] = A[i << 1];
    tem[i+128] = A[(i << 1)+1];
  }

  for (i = 0; i < 128; i++)
  {
#pragma HLS UNROLL
    H[i] = 0;
  }

  for (i = 0; i < 256; i++)
  {
#pragma HLS UNROLL
    t0 = (tem[i] >> 3) & 1;
    t1 = (tem[i] >> 2) & 1;
    t2 = (tem[i] >> 1) & 1;
    t3 = (tem[i] >> 0) & 1;

    H[i>>3] |= t0 << (7 - (i & 7));
    H[(i + 256)>>3] |= t1 << (7 - (i & 7));
    H[(i + 512)>>3] |= t2 << (7 - (i & 7));
    H[(i + 768)>>3] |= t3 << (7 - (i & 7));
  }
}

void R8(uint4 stateIn[256], uint8 roundconstant[32], uint4 stateOut[256])
{
#define L(a, b) {                                                       \
      (b) ^= ( ( (a) << 1) ^ ( (a) >> 3) ^ (( (a) >> 2) & 2) ) & 0xf;   \
      (a) ^= ( ( (b) << 1) ^ ( (b) >> 3) ^ (( (b) >> 2) & 2) ) & 0xf;   \
  }
  int i,j;
  uint1 roundconstant_expanded[256];
  uint4 stateTmp1[256];
  uint4 stateTmp2[256];
  uint4 stateTmp3[256];
  uint4 sbox0[256];
  uint4 sbox1[256];

#pragma HLS INLINE
#pragma HLS ARRAY_RESHAPE variable=stateIn complete dim=1
#pragma HLS ARRAY_RESHAPE variable=stateOut complete dim=1
#pragma HLS ARRAY_RESHAPE variable=roundconstant complete dim=1
#pragma HLS ARRAY_RESHAPE variable=roundconstant_expanded complete dim=1
#pragma HLS ARRAY_RESHAPE variable=stateTmp1 complete dim=1
#pragma HLS ARRAY_RESHAPE variable=stateTmp2 complete dim=1
#pragma HLS ARRAY_RESHAPE variable=stateTmp3 complete dim=1
#pragma HLS ARRAY_RESHAPE variable=sbox0 complete dim=1
#pragma HLS ARRAY_RESHAPE variable=sbox1 complete dim=1
#pragma HLS RESOURCE variable=S0_0 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_1 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_2 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_3 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_4 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_5 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_6 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_7 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_8 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_9 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_10 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_11 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_12 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_13 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_14 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_15 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_16 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_17 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_18 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_19 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_20 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_21 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_22 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_23 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_24 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_25 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_26 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_27 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_28 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_29 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_30 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_31 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_32 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_33 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_34 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_35 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_36 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_37 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_38 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_39 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_40 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_41 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_42 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_43 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_44 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_45 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_46 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_47 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_48 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_49 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_50 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_51 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_52 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_53 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_54 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_55 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_56 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_57 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_58 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_59 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_60 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_61 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_62 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_63 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_64 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_65 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_66 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_67 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_68 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_69 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_70 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_71 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_72 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_73 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_74 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_75 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_76 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_77 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_78 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_79 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_80 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_81 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_82 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_83 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_84 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_85 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_86 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_87 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_88 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_89 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_90 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_91 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_92 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_93 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_94 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_95 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_96 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_97 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_98 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_99 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_100 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_101 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_102 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_103 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_104 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_105 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_106 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_107 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_108 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_109 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_110 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_111 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_112 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_113 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_114 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_115 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_116 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_117 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_118 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_119 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_120 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_121 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_122 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_123 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_124 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_125 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_126 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_127 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_128 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_129 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_130 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_131 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_132 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_133 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_134 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_135 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_136 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_137 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_138 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_139 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_140 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_141 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_142 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_143 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_144 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_145 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_146 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_147 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_148 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_149 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_150 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_151 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_152 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_153 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_154 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_155 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_156 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_157 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_158 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_159 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_160 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_161 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_162 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_163 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_164 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_165 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_166 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_167 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_168 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_169 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_170 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_171 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_172 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_173 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_174 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_175 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_176 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_177 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_178 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_179 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_180 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_181 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_182 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_183 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_184 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_185 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_186 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_187 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_188 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_189 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_190 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_191 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_192 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_193 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_194 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_195 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_196 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_197 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_198 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_199 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_200 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_201 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_202 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_203 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_204 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_205 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_206 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_207 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_208 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_209 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_210 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_211 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_212 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_213 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_214 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_215 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_216 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_217 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_218 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_219 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_220 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_221 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_222 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_223 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_224 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_225 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_226 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_227 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_228 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_229 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_230 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_231 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_232 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_233 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_234 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_235 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_236 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_237 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_238 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_239 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_240 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_241 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_242 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_243 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_244 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_245 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_246 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_247 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_248 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_249 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_250 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_251 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_252 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_253 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_254 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S0_255 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_0 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_1 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_2 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_3 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_4 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_5 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_6 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_7 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_8 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_9 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_10 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_11 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_12 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_13 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_14 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_15 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_16 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_17 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_18 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_19 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_20 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_21 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_22 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_23 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_24 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_25 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_26 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_27 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_28 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_29 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_30 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_31 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_32 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_33 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_34 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_35 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_36 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_37 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_38 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_39 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_40 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_41 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_42 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_43 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_44 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_45 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_46 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_47 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_48 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_49 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_50 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_51 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_52 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_53 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_54 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_55 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_56 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_57 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_58 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_59 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_60 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_61 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_62 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_63 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_64 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_65 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_66 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_67 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_68 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_69 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_70 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_71 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_72 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_73 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_74 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_75 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_76 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_77 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_78 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_79 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_80 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_81 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_82 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_83 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_84 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_85 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_86 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_87 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_88 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_89 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_90 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_91 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_92 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_93 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_94 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_95 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_96 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_97 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_98 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_99 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_100 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_101 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_102 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_103 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_104 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_105 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_106 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_107 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_108 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_109 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_110 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_111 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_112 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_113 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_114 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_115 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_116 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_117 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_118 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_119 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_120 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_121 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_122 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_123 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_124 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_125 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_126 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_127 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_128 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_129 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_130 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_131 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_132 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_133 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_134 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_135 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_136 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_137 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_138 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_139 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_140 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_141 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_142 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_143 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_144 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_145 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_146 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_147 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_148 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_149 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_150 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_151 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_152 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_153 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_154 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_155 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_156 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_157 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_158 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_159 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_160 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_161 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_162 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_163 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_164 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_165 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_166 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_167 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_168 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_169 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_170 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_171 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_172 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_173 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_174 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_175 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_176 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_177 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_178 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_179 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_180 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_181 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_182 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_183 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_184 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_185 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_186 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_187 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_188 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_189 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_190 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_191 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_192 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_193 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_194 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_195 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_196 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_197 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_198 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_199 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_200 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_201 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_202 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_203 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_204 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_205 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_206 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_207 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_208 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_209 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_210 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_211 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_212 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_213 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_214 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_215 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_216 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_217 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_218 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_219 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_220 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_221 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_222 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_223 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_224 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_225 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_226 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_227 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_228 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_229 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_230 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_231 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_232 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_233 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_234 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_235 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_236 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_237 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_238 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_239 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_240 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_241 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_242 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_243 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_244 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_245 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_246 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_247 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_248 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_249 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_250 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_251 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_252 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_253 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_254 core=ROM_1P_1S
#pragma HLS RESOURCE variable=S1_255 core=ROM_1P_1S


#if DEBUG_ROUND
  printf("  ::Initial::\n");
  printState(stateIn);
#endif

  /*expand the round constant into 256 one-bit element*/
  for (i = 0; i < 32; i++)
  {
#pragma HLS UNROLL
    for (j = 0; j < 8; j++)
    {
#pragma HLS UNROLL
      roundconstant_expanded[i*8+j] =  (roundconstant[i] >> (7-j)) & 1;
    }
  }

  /*S box layer, each constant bit selects one Sbox from S0 and S1*/
  sbox0[0] = S0_0[stateIn[0]]; sbox0[1] = S0_1[stateIn[1]];
  sbox0[2] = S0_2[stateIn[2]]; sbox0[3] = S0_3[stateIn[3]];
  sbox0[4] = S0_4[stateIn[4]]; sbox0[5] = S0_5[stateIn[5]];
  sbox0[6] = S0_6[stateIn[6]]; sbox0[7] = S0_7[stateIn[7]];
  sbox0[8] = S0_8[stateIn[8]]; sbox0[9] = S0_9[stateIn[9]];
  sbox0[10] = S0_10[stateIn[10]]; sbox0[11] = S0_11[stateIn[11]];
  sbox0[12] = S0_12[stateIn[12]]; sbox0[13] = S0_13[stateIn[13]];
  sbox0[14] = S0_14[stateIn[14]]; sbox0[15] = S0_15[stateIn[15]];
  sbox0[16] = S0_16[stateIn[16]]; sbox0[17] = S0_17[stateIn[17]];
  sbox0[18] = S0_18[stateIn[18]]; sbox0[19] = S0_19[stateIn[19]];
  sbox0[20] = S0_20[stateIn[20]]; sbox0[21] = S0_21[stateIn[21]];
  sbox0[22] = S0_22[stateIn[22]]; sbox0[23] = S0_23[stateIn[23]];
  sbox0[24] = S0_24[stateIn[24]]; sbox0[25] = S0_25[stateIn[25]];
  sbox0[26] = S0_26[stateIn[26]]; sbox0[27] = S0_27[stateIn[27]];
  sbox0[28] = S0_28[stateIn[28]]; sbox0[29] = S0_29[stateIn[29]];
  sbox0[30] = S0_30[stateIn[30]]; sbox0[31] = S0_31[stateIn[31]];
  sbox0[32] = S0_32[stateIn[32]]; sbox0[33] = S0_33[stateIn[33]];
  sbox0[34] = S0_34[stateIn[34]]; sbox0[35] = S0_35[stateIn[35]];
  sbox0[36] = S0_36[stateIn[36]]; sbox0[37] = S0_37[stateIn[37]];
  sbox0[38] = S0_38[stateIn[38]]; sbox0[39] = S0_39[stateIn[39]];
  sbox0[40] = S0_40[stateIn[40]]; sbox0[41] = S0_41[stateIn[41]];
  sbox0[42] = S0_42[stateIn[42]]; sbox0[43] = S0_43[stateIn[43]];
  sbox0[44] = S0_44[stateIn[44]]; sbox0[45] = S0_45[stateIn[45]];
  sbox0[46] = S0_46[stateIn[46]]; sbox0[47] = S0_47[stateIn[47]];
  sbox0[48] = S0_48[stateIn[48]]; sbox0[49] = S0_49[stateIn[49]];
  sbox0[50] = S0_50[stateIn[50]]; sbox0[51] = S0_51[stateIn[51]];
  sbox0[52] = S0_52[stateIn[52]]; sbox0[53] = S0_53[stateIn[53]];
  sbox0[54] = S0_54[stateIn[54]]; sbox0[55] = S0_55[stateIn[55]];
  sbox0[56] = S0_56[stateIn[56]]; sbox0[57] = S0_57[stateIn[57]];
  sbox0[58] = S0_58[stateIn[58]]; sbox0[59] = S0_59[stateIn[59]];
  sbox0[60] = S0_60[stateIn[60]]; sbox0[61] = S0_61[stateIn[61]];
  sbox0[62] = S0_62[stateIn[62]]; sbox0[63] = S0_63[stateIn[63]];
  sbox0[64] = S0_64[stateIn[64]]; sbox0[65] = S0_65[stateIn[65]];
  sbox0[66] = S0_66[stateIn[66]]; sbox0[67] = S0_67[stateIn[67]];
  sbox0[68] = S0_68[stateIn[68]]; sbox0[69] = S0_69[stateIn[69]];
  sbox0[70] = S0_70[stateIn[70]]; sbox0[71] = S0_71[stateIn[71]];
  sbox0[72] = S0_72[stateIn[72]]; sbox0[73] = S0_73[stateIn[73]];
  sbox0[74] = S0_74[stateIn[74]]; sbox0[75] = S0_75[stateIn[75]];
  sbox0[76] = S0_76[stateIn[76]]; sbox0[77] = S0_77[stateIn[77]];
  sbox0[78] = S0_78[stateIn[78]]; sbox0[79] = S0_79[stateIn[79]];
  sbox0[80] = S0_80[stateIn[80]]; sbox0[81] = S0_81[stateIn[81]];
  sbox0[82] = S0_82[stateIn[82]]; sbox0[83] = S0_83[stateIn[83]];
  sbox0[84] = S0_84[stateIn[84]]; sbox0[85] = S0_85[stateIn[85]];
  sbox0[86] = S0_86[stateIn[86]]; sbox0[87] = S0_87[stateIn[87]];
  sbox0[88] = S0_88[stateIn[88]]; sbox0[89] = S0_89[stateIn[89]];
  sbox0[90] = S0_90[stateIn[90]]; sbox0[91] = S0_91[stateIn[91]];
  sbox0[92] = S0_92[stateIn[92]]; sbox0[93] = S0_93[stateIn[93]];
  sbox0[94] = S0_94[stateIn[94]]; sbox0[95] = S0_95[stateIn[95]];
  sbox0[96] = S0_96[stateIn[96]]; sbox0[97] = S0_97[stateIn[97]];
  sbox0[98] = S0_98[stateIn[98]]; sbox0[99] = S0_99[stateIn[99]];
  sbox0[100] = S0_100[stateIn[100]]; sbox0[101] = S0_101[stateIn[101]];
  sbox0[102] = S0_102[stateIn[102]]; sbox0[103] = S0_103[stateIn[103]];
  sbox0[104] = S0_104[stateIn[104]]; sbox0[105] = S0_105[stateIn[105]];
  sbox0[106] = S0_106[stateIn[106]]; sbox0[107] = S0_107[stateIn[107]];
  sbox0[108] = S0_108[stateIn[108]]; sbox0[109] = S0_109[stateIn[109]];
  sbox0[110] = S0_110[stateIn[110]]; sbox0[111] = S0_111[stateIn[111]];
  sbox0[112] = S0_112[stateIn[112]]; sbox0[113] = S0_113[stateIn[113]];
  sbox0[114] = S0_114[stateIn[114]]; sbox0[115] = S0_115[stateIn[115]];
  sbox0[116] = S0_116[stateIn[116]]; sbox0[117] = S0_117[stateIn[117]];
  sbox0[118] = S0_118[stateIn[118]]; sbox0[119] = S0_119[stateIn[119]];
  sbox0[120] = S0_120[stateIn[120]]; sbox0[121] = S0_121[stateIn[121]];
  sbox0[122] = S0_122[stateIn[122]]; sbox0[123] = S0_123[stateIn[123]];
  sbox0[124] = S0_124[stateIn[124]]; sbox0[125] = S0_125[stateIn[125]];
  sbox0[126] = S0_126[stateIn[126]]; sbox0[127] = S0_127[stateIn[127]];
  sbox0[128] = S0_128[stateIn[128]]; sbox0[129] = S0_129[stateIn[129]];
  sbox0[130] = S0_130[stateIn[130]]; sbox0[131] = S0_131[stateIn[131]];
  sbox0[132] = S0_132[stateIn[132]]; sbox0[133] = S0_133[stateIn[133]];
  sbox0[134] = S0_134[stateIn[134]]; sbox0[135] = S0_135[stateIn[135]];
  sbox0[136] = S0_136[stateIn[136]]; sbox0[137] = S0_137[stateIn[137]];
  sbox0[138] = S0_138[stateIn[138]]; sbox0[139] = S0_139[stateIn[139]];
  sbox0[140] = S0_140[stateIn[140]]; sbox0[141] = S0_141[stateIn[141]];
  sbox0[142] = S0_142[stateIn[142]]; sbox0[143] = S0_143[stateIn[143]];
  sbox0[144] = S0_144[stateIn[144]]; sbox0[145] = S0_145[stateIn[145]];
  sbox0[146] = S0_146[stateIn[146]]; sbox0[147] = S0_147[stateIn[147]];
  sbox0[148] = S0_148[stateIn[148]]; sbox0[149] = S0_149[stateIn[149]];
  sbox0[150] = S0_150[stateIn[150]]; sbox0[151] = S0_151[stateIn[151]];
  sbox0[152] = S0_152[stateIn[152]]; sbox0[153] = S0_153[stateIn[153]];
  sbox0[154] = S0_154[stateIn[154]]; sbox0[155] = S0_155[stateIn[155]];
  sbox0[156] = S0_156[stateIn[156]]; sbox0[157] = S0_157[stateIn[157]];
  sbox0[158] = S0_158[stateIn[158]]; sbox0[159] = S0_159[stateIn[159]];
  sbox0[160] = S0_160[stateIn[160]]; sbox0[161] = S0_161[stateIn[161]];
  sbox0[162] = S0_162[stateIn[162]]; sbox0[163] = S0_163[stateIn[163]];
  sbox0[164] = S0_164[stateIn[164]]; sbox0[165] = S0_165[stateIn[165]];
  sbox0[166] = S0_166[stateIn[166]]; sbox0[167] = S0_167[stateIn[167]];
  sbox0[168] = S0_168[stateIn[168]]; sbox0[169] = S0_169[stateIn[169]];
  sbox0[170] = S0_170[stateIn[170]]; sbox0[171] = S0_171[stateIn[171]];
  sbox0[172] = S0_172[stateIn[172]]; sbox0[173] = S0_173[stateIn[173]];
  sbox0[174] = S0_174[stateIn[174]]; sbox0[175] = S0_175[stateIn[175]];
  sbox0[176] = S0_176[stateIn[176]]; sbox0[177] = S0_177[stateIn[177]];
  sbox0[178] = S0_178[stateIn[178]]; sbox0[179] = S0_179[stateIn[179]];
  sbox0[180] = S0_180[stateIn[180]]; sbox0[181] = S0_181[stateIn[181]];
  sbox0[182] = S0_182[stateIn[182]]; sbox0[183] = S0_183[stateIn[183]];
  sbox0[184] = S0_184[stateIn[184]]; sbox0[185] = S0_185[stateIn[185]];
  sbox0[186] = S0_186[stateIn[186]]; sbox0[187] = S0_187[stateIn[187]];
  sbox0[188] = S0_188[stateIn[188]]; sbox0[189] = S0_189[stateIn[189]];
  sbox0[190] = S0_190[stateIn[190]]; sbox0[191] = S0_191[stateIn[191]];
  sbox0[192] = S0_192[stateIn[192]]; sbox0[193] = S0_193[stateIn[193]];
  sbox0[194] = S0_194[stateIn[194]]; sbox0[195] = S0_195[stateIn[195]];
  sbox0[196] = S0_196[stateIn[196]]; sbox0[197] = S0_197[stateIn[197]];
  sbox0[198] = S0_198[stateIn[198]]; sbox0[199] = S0_199[stateIn[199]];
  sbox0[200] = S0_200[stateIn[200]]; sbox0[201] = S0_201[stateIn[201]];
  sbox0[202] = S0_202[stateIn[202]]; sbox0[203] = S0_203[stateIn[203]];
  sbox0[204] = S0_204[stateIn[204]]; sbox0[205] = S0_205[stateIn[205]];
  sbox0[206] = S0_206[stateIn[206]]; sbox0[207] = S0_207[stateIn[207]];
  sbox0[208] = S0_208[stateIn[208]]; sbox0[209] = S0_209[stateIn[209]];
  sbox0[210] = S0_210[stateIn[210]]; sbox0[211] = S0_211[stateIn[211]];
  sbox0[212] = S0_212[stateIn[212]]; sbox0[213] = S0_213[stateIn[213]];
  sbox0[214] = S0_214[stateIn[214]]; sbox0[215] = S0_215[stateIn[215]];
  sbox0[216] = S0_216[stateIn[216]]; sbox0[217] = S0_217[stateIn[217]];
  sbox0[218] = S0_218[stateIn[218]]; sbox0[219] = S0_219[stateIn[219]];
  sbox0[220] = S0_220[stateIn[220]]; sbox0[221] = S0_221[stateIn[221]];
  sbox0[222] = S0_222[stateIn[222]]; sbox0[223] = S0_223[stateIn[223]];
  sbox0[224] = S0_224[stateIn[224]]; sbox0[225] = S0_225[stateIn[225]];
  sbox0[226] = S0_226[stateIn[226]]; sbox0[227] = S0_227[stateIn[227]];
  sbox0[228] = S0_228[stateIn[228]]; sbox0[229] = S0_229[stateIn[229]];
  sbox0[230] = S0_230[stateIn[230]]; sbox0[231] = S0_231[stateIn[231]];
  sbox0[232] = S0_232[stateIn[232]]; sbox0[233] = S0_233[stateIn[233]];
  sbox0[234] = S0_234[stateIn[234]]; sbox0[235] = S0_235[stateIn[235]];
  sbox0[236] = S0_236[stateIn[236]]; sbox0[237] = S0_237[stateIn[237]];
  sbox0[238] = S0_238[stateIn[238]]; sbox0[239] = S0_239[stateIn[239]];
  sbox0[240] = S0_240[stateIn[240]]; sbox0[241] = S0_241[stateIn[241]];
  sbox0[242] = S0_242[stateIn[242]]; sbox0[243] = S0_243[stateIn[243]];
  sbox0[244] = S0_244[stateIn[244]]; sbox0[245] = S0_245[stateIn[245]];
  sbox0[246] = S0_246[stateIn[246]]; sbox0[247] = S0_247[stateIn[247]];
  sbox0[248] = S0_248[stateIn[248]]; sbox0[249] = S0_249[stateIn[249]];
  sbox0[250] = S0_250[stateIn[250]]; sbox0[251] = S0_251[stateIn[251]];
  sbox0[252] = S0_252[stateIn[252]]; sbox0[253] = S0_253[stateIn[253]];
  sbox0[254] = S0_254[stateIn[254]]; sbox0[255] = S0_255[stateIn[255]];
  sbox1[0] = S1_0[stateIn[0]]; sbox1[1] = S1_1[stateIn[1]];
  sbox1[2] = S1_2[stateIn[2]]; sbox1[3] = S1_3[stateIn[3]];
  sbox1[4] = S1_4[stateIn[4]]; sbox1[5] = S1_5[stateIn[5]];
  sbox1[6] = S1_6[stateIn[6]]; sbox1[7] = S1_7[stateIn[7]];
  sbox1[8] = S1_8[stateIn[8]]; sbox1[9] = S1_9[stateIn[9]];
  sbox1[10] = S1_10[stateIn[10]]; sbox1[11] = S1_11[stateIn[11]];
  sbox1[12] = S1_12[stateIn[12]]; sbox1[13] = S1_13[stateIn[13]];
  sbox1[14] = S1_14[stateIn[14]]; sbox1[15] = S1_15[stateIn[15]];
  sbox1[16] = S1_16[stateIn[16]]; sbox1[17] = S1_17[stateIn[17]];
  sbox1[18] = S1_18[stateIn[18]]; sbox1[19] = S1_19[stateIn[19]];
  sbox1[20] = S1_20[stateIn[20]]; sbox1[21] = S1_21[stateIn[21]];
  sbox1[22] = S1_22[stateIn[22]]; sbox1[23] = S1_23[stateIn[23]];
  sbox1[24] = S1_24[stateIn[24]]; sbox1[25] = S1_25[stateIn[25]];
  sbox1[26] = S1_26[stateIn[26]]; sbox1[27] = S1_27[stateIn[27]];
  sbox1[28] = S1_28[stateIn[28]]; sbox1[29] = S1_29[stateIn[29]];
  sbox1[30] = S1_30[stateIn[30]]; sbox1[31] = S1_31[stateIn[31]];
  sbox1[32] = S1_32[stateIn[32]]; sbox1[33] = S1_33[stateIn[33]];
  sbox1[34] = S1_34[stateIn[34]]; sbox1[35] = S1_35[stateIn[35]];
  sbox1[36] = S1_36[stateIn[36]]; sbox1[37] = S1_37[stateIn[37]];
  sbox1[38] = S1_38[stateIn[38]]; sbox1[39] = S1_39[stateIn[39]];
  sbox1[40] = S1_40[stateIn[40]]; sbox1[41] = S1_41[stateIn[41]];
  sbox1[42] = S1_42[stateIn[42]]; sbox1[43] = S1_43[stateIn[43]];
  sbox1[44] = S1_44[stateIn[44]]; sbox1[45] = S1_45[stateIn[45]];
  sbox1[46] = S1_46[stateIn[46]]; sbox1[47] = S1_47[stateIn[47]];
  sbox1[48] = S1_48[stateIn[48]]; sbox1[49] = S1_49[stateIn[49]];
  sbox1[50] = S1_50[stateIn[50]]; sbox1[51] = S1_51[stateIn[51]];
  sbox1[52] = S1_52[stateIn[52]]; sbox1[53] = S1_53[stateIn[53]];
  sbox1[54] = S1_54[stateIn[54]]; sbox1[55] = S1_55[stateIn[55]];
  sbox1[56] = S1_56[stateIn[56]]; sbox1[57] = S1_57[stateIn[57]];
  sbox1[58] = S1_58[stateIn[58]]; sbox1[59] = S1_59[stateIn[59]];
  sbox1[60] = S1_60[stateIn[60]]; sbox1[61] = S1_61[stateIn[61]];
  sbox1[62] = S1_62[stateIn[62]]; sbox1[63] = S1_63[stateIn[63]];
  sbox1[64] = S1_64[stateIn[64]]; sbox1[65] = S1_65[stateIn[65]];
  sbox1[66] = S1_66[stateIn[66]]; sbox1[67] = S1_67[stateIn[67]];
  sbox1[68] = S1_68[stateIn[68]]; sbox1[69] = S1_69[stateIn[69]];
  sbox1[70] = S1_70[stateIn[70]]; sbox1[71] = S1_71[stateIn[71]];
  sbox1[72] = S1_72[stateIn[72]]; sbox1[73] = S1_73[stateIn[73]];
  sbox1[74] = S1_74[stateIn[74]]; sbox1[75] = S1_75[stateIn[75]];
  sbox1[76] = S1_76[stateIn[76]]; sbox1[77] = S1_77[stateIn[77]];
  sbox1[78] = S1_78[stateIn[78]]; sbox1[79] = S1_79[stateIn[79]];
  sbox1[80] = S1_80[stateIn[80]]; sbox1[81] = S1_81[stateIn[81]];
  sbox1[82] = S1_82[stateIn[82]]; sbox1[83] = S1_83[stateIn[83]];
  sbox1[84] = S1_84[stateIn[84]]; sbox1[85] = S1_85[stateIn[85]];
  sbox1[86] = S1_86[stateIn[86]]; sbox1[87] = S1_87[stateIn[87]];
  sbox1[88] = S1_88[stateIn[88]]; sbox1[89] = S1_89[stateIn[89]];
  sbox1[90] = S1_90[stateIn[90]]; sbox1[91] = S1_91[stateIn[91]];
  sbox1[92] = S1_92[stateIn[92]]; sbox1[93] = S1_93[stateIn[93]];
  sbox1[94] = S1_94[stateIn[94]]; sbox1[95] = S1_95[stateIn[95]];
  sbox1[96] = S1_96[stateIn[96]]; sbox1[97] = S1_97[stateIn[97]];
  sbox1[98] = S1_98[stateIn[98]]; sbox1[99] = S1_99[stateIn[99]];
  sbox1[100] = S1_100[stateIn[100]]; sbox1[101] = S1_101[stateIn[101]];
  sbox1[102] = S1_102[stateIn[102]]; sbox1[103] = S1_103[stateIn[103]];
  sbox1[104] = S1_104[stateIn[104]]; sbox1[105] = S1_105[stateIn[105]];
  sbox1[106] = S1_106[stateIn[106]]; sbox1[107] = S1_107[stateIn[107]];
  sbox1[108] = S1_108[stateIn[108]]; sbox1[109] = S1_109[stateIn[109]];
  sbox1[110] = S1_110[stateIn[110]]; sbox1[111] = S1_111[stateIn[111]];
  sbox1[112] = S1_112[stateIn[112]]; sbox1[113] = S1_113[stateIn[113]];
  sbox1[114] = S1_114[stateIn[114]]; sbox1[115] = S1_115[stateIn[115]];
  sbox1[116] = S1_116[stateIn[116]]; sbox1[117] = S1_117[stateIn[117]];
  sbox1[118] = S1_118[stateIn[118]]; sbox1[119] = S1_119[stateIn[119]];
  sbox1[120] = S1_120[stateIn[120]]; sbox1[121] = S1_121[stateIn[121]];
  sbox1[122] = S1_122[stateIn[122]]; sbox1[123] = S1_123[stateIn[123]];
  sbox1[124] = S1_124[stateIn[124]]; sbox1[125] = S1_125[stateIn[125]];
  sbox1[126] = S1_126[stateIn[126]]; sbox1[127] = S1_127[stateIn[127]];
  sbox1[128] = S1_128[stateIn[128]]; sbox1[129] = S1_129[stateIn[129]];
  sbox1[130] = S1_130[stateIn[130]]; sbox1[131] = S1_131[stateIn[131]];
  sbox1[132] = S1_132[stateIn[132]]; sbox1[133] = S1_133[stateIn[133]];
  sbox1[134] = S1_134[stateIn[134]]; sbox1[135] = S1_135[stateIn[135]];
  sbox1[136] = S1_136[stateIn[136]]; sbox1[137] = S1_137[stateIn[137]];
  sbox1[138] = S1_138[stateIn[138]]; sbox1[139] = S1_139[stateIn[139]];
  sbox1[140] = S1_140[stateIn[140]]; sbox1[141] = S1_141[stateIn[141]];
  sbox1[142] = S1_142[stateIn[142]]; sbox1[143] = S1_143[stateIn[143]];
  sbox1[144] = S1_144[stateIn[144]]; sbox1[145] = S1_145[stateIn[145]];
  sbox1[146] = S1_146[stateIn[146]]; sbox1[147] = S1_147[stateIn[147]];
  sbox1[148] = S1_148[stateIn[148]]; sbox1[149] = S1_149[stateIn[149]];
  sbox1[150] = S1_150[stateIn[150]]; sbox1[151] = S1_151[stateIn[151]];
  sbox1[152] = S1_152[stateIn[152]]; sbox1[153] = S1_153[stateIn[153]];
  sbox1[154] = S1_154[stateIn[154]]; sbox1[155] = S1_155[stateIn[155]];
  sbox1[156] = S1_156[stateIn[156]]; sbox1[157] = S1_157[stateIn[157]];
  sbox1[158] = S1_158[stateIn[158]]; sbox1[159] = S1_159[stateIn[159]];
  sbox1[160] = S1_160[stateIn[160]]; sbox1[161] = S1_161[stateIn[161]];
  sbox1[162] = S1_162[stateIn[162]]; sbox1[163] = S1_163[stateIn[163]];
  sbox1[164] = S1_164[stateIn[164]]; sbox1[165] = S1_165[stateIn[165]];
  sbox1[166] = S1_166[stateIn[166]]; sbox1[167] = S1_167[stateIn[167]];
  sbox1[168] = S1_168[stateIn[168]]; sbox1[169] = S1_169[stateIn[169]];
  sbox1[170] = S1_170[stateIn[170]]; sbox1[171] = S1_171[stateIn[171]];
  sbox1[172] = S1_172[stateIn[172]]; sbox1[173] = S1_173[stateIn[173]];
  sbox1[174] = S1_174[stateIn[174]]; sbox1[175] = S1_175[stateIn[175]];
  sbox1[176] = S1_176[stateIn[176]]; sbox1[177] = S1_177[stateIn[177]];
  sbox1[178] = S1_178[stateIn[178]]; sbox1[179] = S1_179[stateIn[179]];
  sbox1[180] = S1_180[stateIn[180]]; sbox1[181] = S1_181[stateIn[181]];
  sbox1[182] = S1_182[stateIn[182]]; sbox1[183] = S1_183[stateIn[183]];
  sbox1[184] = S1_184[stateIn[184]]; sbox1[185] = S1_185[stateIn[185]];
  sbox1[186] = S1_186[stateIn[186]]; sbox1[187] = S1_187[stateIn[187]];
  sbox1[188] = S1_188[stateIn[188]]; sbox1[189] = S1_189[stateIn[189]];
  sbox1[190] = S1_190[stateIn[190]]; sbox1[191] = S1_191[stateIn[191]];
  sbox1[192] = S1_192[stateIn[192]]; sbox1[193] = S1_193[stateIn[193]];
  sbox1[194] = S1_194[stateIn[194]]; sbox1[195] = S1_195[stateIn[195]];
  sbox1[196] = S1_196[stateIn[196]]; sbox1[197] = S1_197[stateIn[197]];
  sbox1[198] = S1_198[stateIn[198]]; sbox1[199] = S1_199[stateIn[199]];
  sbox1[200] = S1_200[stateIn[200]]; sbox1[201] = S1_201[stateIn[201]];
  sbox1[202] = S1_202[stateIn[202]]; sbox1[203] = S1_203[stateIn[203]];
  sbox1[204] = S1_204[stateIn[204]]; sbox1[205] = S1_205[stateIn[205]];
  sbox1[206] = S1_206[stateIn[206]]; sbox1[207] = S1_207[stateIn[207]];
  sbox1[208] = S1_208[stateIn[208]]; sbox1[209] = S1_209[stateIn[209]];
  sbox1[210] = S1_210[stateIn[210]]; sbox1[211] = S1_211[stateIn[211]];
  sbox1[212] = S1_212[stateIn[212]]; sbox1[213] = S1_213[stateIn[213]];
  sbox1[214] = S1_214[stateIn[214]]; sbox1[215] = S1_215[stateIn[215]];
  sbox1[216] = S1_216[stateIn[216]]; sbox1[217] = S1_217[stateIn[217]];
  sbox1[218] = S1_218[stateIn[218]]; sbox1[219] = S1_219[stateIn[219]];
  sbox1[220] = S1_220[stateIn[220]]; sbox1[221] = S1_221[stateIn[221]];
  sbox1[222] = S1_222[stateIn[222]]; sbox1[223] = S1_223[stateIn[223]];
  sbox1[224] = S1_224[stateIn[224]]; sbox1[225] = S1_225[stateIn[225]];
  sbox1[226] = S1_226[stateIn[226]]; sbox1[227] = S1_227[stateIn[227]];
  sbox1[228] = S1_228[stateIn[228]]; sbox1[229] = S1_229[stateIn[229]];
  sbox1[230] = S1_230[stateIn[230]]; sbox1[231] = S1_231[stateIn[231]];
  sbox1[232] = S1_232[stateIn[232]]; sbox1[233] = S1_233[stateIn[233]];
  sbox1[234] = S1_234[stateIn[234]]; sbox1[235] = S1_235[stateIn[235]];
  sbox1[236] = S1_236[stateIn[236]]; sbox1[237] = S1_237[stateIn[237]];
  sbox1[238] = S1_238[stateIn[238]]; sbox1[239] = S1_239[stateIn[239]];
  sbox1[240] = S1_240[stateIn[240]]; sbox1[241] = S1_241[stateIn[241]];
  sbox1[242] = S1_242[stateIn[242]]; sbox1[243] = S1_243[stateIn[243]];
  sbox1[244] = S1_244[stateIn[244]]; sbox1[245] = S1_245[stateIn[245]];
  sbox1[246] = S1_246[stateIn[246]]; sbox1[247] = S1_247[stateIn[247]];
  sbox1[248] = S1_248[stateIn[248]]; sbox1[249] = S1_249[stateIn[249]];
  sbox1[250] = S1_250[stateIn[250]]; sbox1[251] = S1_251[stateIn[251]];
  sbox1[252] = S1_252[stateIn[252]]; sbox1[253] = S1_253[stateIn[253]];
  sbox1[254] = S1_254[stateIn[254]]; sbox1[255] = S1_255[stateIn[255]];

  for (i = 0; i < 256; i++)
  {
#pragma HLS UNROLL
    if (roundconstant_expanded[i] == 1)
      stateTmp1[i] = sbox1[i];
    else
      stateTmp1[i] = sbox0[i];
  }

#if DEBUG_ROUND
  printf("  ::After SBOX::\n");
  printState(stateTmp1);
#endif

  /*MDS Layer*/
   for (i = 0; i < 256; i=i+2)
   {
#pragma HLS UNROLL
     L(stateTmp1[i], stateTmp1[i+1]);
   }

#if DEBUG_ROUND
  printf("  ::After MDS Layer::\n");
  printState(stateTmp1);
#endif

  /*The following is the permuation layer P_8$*/
  /*initial swap Pi_8*/
  for ( i = 0; i < 256; i=i+4)
  {
#pragma HLS UNROLL
    stateTmp2[i+0] = stateTmp1[i+0];
    stateTmp2[i+1] = stateTmp1[i+1];
    stateTmp2[i+2] = stateTmp1[i+3];
    stateTmp2[i+3] = stateTmp1[i+2];
  }

  /*permutation P'_8*/
  for (i = 0; i < 128; i=i+1)
  {
#pragma HLS UNROLL
    stateTmp3[i] = stateTmp2[i<<1];
    stateTmp3[i+128] = stateTmp2[(i<<1)+1];
  }

  /*final swap Phi_8*/
  for ( i = 128; i < 256; i=i+2)
  {
#pragma HLS UNROLL
    // Hi
    stateOut[i-128]   = stateTmp3[i-128];
    stateOut[i-128+1] = stateTmp3[i-128+1];
    // Lo
    stateOut[i]     = stateTmp3[i+1];
    stateOut[i+1]   = stateTmp3[i];
  }
}

void getRoundConstant(uint8 round, uint8 roundconstant[32])
{
  uint8 rc_rom[42][32] = {
        //{0x6a, 0x09, 0xe6, 0x67, 0xf3, 0xbc, 0xc9, 0x08, 0xb2, 0xfb, 0x13, 0x66, 0xea, 0x95, 0x7d, 0x3e, 0x3a, 0xde, 0xc1, 0x75, 0x12, 0x77, 0x50, 0x99, 0xda, 0x2f, 0x59, 0x0b, 0x06, 0x67, 0x32, 0x2a},
        {0xbb, 0x89, 0x6b, 0xf0, 0x59, 0x55, 0xab, 0xcd, 0x52, 0x81, 0x82, 0x8d, 0x66, 0xe7, 0xd9, 0x9a, 0xc4, 0x20, 0x34, 0x94, 0xf8, 0x9b, 0xf1, 0x28, 0x17, 0xde, 0xb4, 0x32, 0x88, 0x71, 0x22, 0x31},
        {0x18, 0x36, 0xe7, 0x6b, 0x12, 0xd7, 0x9c, 0x55, 0x11, 0x8a, 0x11, 0x39, 0xd2, 0x41, 0x7d, 0xf5, 0x2a, 0x20, 0x21, 0x22, 0x5f, 0xf6, 0x35, 0x00, 0x63, 0xd8, 0x8e, 0x5f, 0x1f, 0x91, 0x63, 0x1c},
        {0x26, 0x30, 0x85, 0xa7, 0x00, 0x0f, 0xa9, 0xc3, 0x31, 0x7c, 0x6c, 0xa8, 0xab, 0x65, 0xf7, 0xa7, 0x71, 0x3c, 0xf4, 0x20, 0x10, 0x60, 0xce, 0x88, 0x6a, 0xf8, 0x55, 0xa9, 0x0d, 0x6a, 0x4e, 0xed},
        {0x1c, 0xeb, 0xaf, 0xd5, 0x1a, 0x15, 0x6a, 0xeb, 0x62, 0xa1, 0x1f, 0xb3, 0xbe, 0x2e, 0x14, 0xf6, 0x0b, 0x7e, 0x48, 0xde, 0x85, 0x81, 0x42, 0x70, 0xfd, 0x62, 0xe9, 0x76, 0x14, 0xd7, 0xb4, 0x41},
        {0xe5, 0x56, 0x4c, 0xb5, 0x74, 0xf7, 0xe0, 0x9c, 0x75, 0xe2, 0xe2, 0x44, 0x92, 0x9e, 0x95, 0x49, 0x27, 0x9a, 0xb2, 0x24, 0xa2, 0x8e, 0x44, 0x5d, 0x57, 0x18, 0x5e, 0x7d, 0x7a, 0x09, 0xfd, 0xc1},
        {0x58, 0x20, 0xf0, 0xf0, 0xd7, 0x64, 0xcf, 0xf3, 0xa5, 0x55, 0x2a, 0x5e, 0x41, 0xa8, 0x2b, 0x9e, 0xff, 0x6e, 0xe0, 0xaa, 0x61, 0x57, 0x73, 0xbb, 0x07, 0xe8, 0x60, 0x34, 0x24, 0xc3, 0xcf, 0x8a},
        {0xb1, 0x26, 0xfb, 0x74, 0x17, 0x33, 0xc5, 0xbf, 0xce, 0xf6, 0xf4, 0x3a, 0x62, 0xe8, 0xe5, 0x70, 0x6a, 0x26, 0x65, 0x60, 0x28, 0xaa, 0x89, 0x7e, 0xc1, 0xea, 0x46, 0x16, 0xce, 0x8f, 0xd5, 0x10},
        {0xdb, 0xf0, 0xde, 0x32, 0xbc, 0xa7, 0x72, 0x54, 0xbb, 0x4f, 0x56, 0x25, 0x81, 0xa3, 0xbc, 0x99, 0x1c, 0xf9, 0x4f, 0x22, 0x56, 0x52, 0xc2, 0x7f, 0x14, 0xea, 0xe9, 0x58, 0xae, 0x6a, 0xa6, 0x16},
        {0xe6, 0x11, 0x3b, 0xe6, 0x17, 0xf4, 0x5f, 0x3d, 0xe5, 0x3c, 0xff, 0x03, 0x91, 0x9a, 0x94, 0xc3, 0x2c, 0x92, 0x7b, 0x09, 0x3a, 0xc8, 0xf2, 0x3b, 0x47, 0xf7, 0x18, 0x9a, 0xad, 0xb9, 0xbc, 0x67},
        {0x80, 0xd0, 0xd2, 0x60, 0x52, 0xca, 0x45, 0xd5, 0x93, 0xab, 0x5f, 0xb3, 0x10, 0x25, 0x06, 0x39, 0x00, 0x83, 0xaf, 0xb5, 0xff, 0xe1, 0x07, 0xda, 0xcf, 0xcb, 0xa7, 0xdb, 0xe6, 0x01, 0xa1, 0x2b},
        {0x43, 0xaf, 0x1c, 0x76, 0x12, 0x67, 0x14, 0xdf, 0xa9, 0x50, 0xc3, 0x68, 0x78, 0x7c, 0x81, 0xae, 0x3b, 0xee, 0xcf, 0x95, 0x6c, 0x85, 0xc9, 0x62, 0x08, 0x6a, 0xe1, 0x6e, 0x40, 0xeb, 0xb0, 0xb4},
        {0x9a, 0xee, 0x89, 0x94, 0xd2, 0xd7, 0x4a, 0x5c, 0xdb, 0x7b, 0x1e, 0xf2, 0x94, 0xee, 0xd5, 0xc1, 0x52, 0x07, 0x24, 0xdd, 0x8e, 0xd5, 0x8c, 0x92, 0xd3, 0xf0, 0xe1, 0x74, 0xb0, 0xc3, 0x20, 0x45},
        {0x0b, 0x2a, 0xa5, 0x8c, 0xeb, 0x3b, 0xdb, 0x9e, 0x1e, 0xef, 0x66, 0xb3, 0x76, 0xe0, 0xc5, 0x65, 0xd5, 0xd8, 0xfe, 0x7b, 0xac, 0xb8, 0xda, 0x86, 0x6f, 0x85, 0x9a, 0xc5, 0x21, 0xf3, 0xd5, 0x71},
        {0x7a, 0x15, 0x23, 0xef, 0x3d, 0x97, 0x0a, 0x3a, 0x9b, 0x0b, 0x4d, 0x61, 0x0e, 0x02, 0x74, 0x9d, 0x37, 0xb8, 0xd5, 0x7c, 0x18, 0x85, 0xfe, 0x42, 0x06, 0xa7, 0xf3, 0x38, 0xe8, 0x35, 0x68, 0x66},
        {0x2c, 0x2d, 0xb8, 0xf7, 0x87, 0x66, 0x85, 0xf2, 0xcd, 0x9a, 0x2e, 0x0d, 0xdb, 0x64, 0xc9, 0xd5, 0xbf, 0x13, 0x90, 0x53, 0x71, 0xfc, 0x39, 0xe0, 0xfa, 0x86, 0xe1, 0x47, 0x72, 0x34, 0xa2, 0x97},
        {0x9d, 0xf0, 0x85, 0xeb, 0x25, 0x44, 0xeb, 0xf6, 0x2b, 0x50, 0x68, 0x6a, 0x71, 0xe6, 0xe8, 0x28, 0xdf, 0xed, 0x9d, 0xbe, 0x0b, 0x10, 0x6c, 0x94, 0x52, 0xce, 0xdd, 0xff, 0x3d, 0x13, 0x89, 0x90},
        {0xe6, 0xe5, 0xc4, 0x2c, 0xb2, 0xd4, 0x60, 0xc9, 0xd6, 0xe4, 0x79, 0x1a, 0x16, 0x81, 0xbb, 0x2e, 0x22, 0x2e, 0x54, 0x55, 0x8e, 0xb7, 0x8d, 0x52, 0x44, 0xe2, 0x17, 0xd1, 0xbf, 0xcf, 0x50, 0x58},
        {0x8f, 0x1f, 0x57, 0xe4, 0x4e, 0x12, 0x62, 0x10, 0xf0, 0x07, 0x63, 0xff, 0x57, 0xda, 0x20, 0x8a, 0x50, 0x93, 0xb8, 0xff, 0x79, 0x47, 0x53, 0x4a, 0x4c, 0x26, 0x0a, 0x17, 0x64, 0x2f, 0x72, 0xb2},
        {0xae, 0x4e, 0xf4, 0x79, 0x2e, 0xa1, 0x48, 0x60, 0x8c, 0xf1, 0x16, 0xcb, 0x2b, 0xff, 0x66, 0xe8, 0xfc, 0x74, 0x81, 0x12, 0x66, 0xcd, 0x64, 0x11, 0x12, 0xcd, 0x17, 0x80, 0x1e, 0xd3, 0x8b, 0x59},
        {0x91, 0xa7, 0x44, 0xef, 0xbf, 0x68, 0xb1, 0x92, 0xd0, 0x54, 0x9b, 0x60, 0x8b, 0xdb, 0x31, 0x91, 0xfc, 0x12, 0xa0, 0xe8, 0x35, 0x43, 0xce, 0xc5, 0xf8, 0x82, 0x25, 0x0b, 0x24, 0x4f, 0x78, 0xe4},
        {0x4b, 0x5d, 0x27, 0xd3, 0x36, 0x8f, 0x9c, 0x17, 0xd4, 0xb2, 0xa2, 0xb2, 0x16, 0xc7, 0xe7, 0x4e, 0x77, 0x14, 0xd2, 0xcc, 0x03, 0xe1, 0xe4, 0x45, 0x88, 0xcd, 0x99, 0x36, 0xde, 0x74, 0x35, 0x7c},
        {0x0e, 0xa1, 0x7c, 0xaf, 0xb8, 0x28, 0x61, 0x31, 0xbd, 0xa9, 0xe3, 0x75, 0x7b, 0x36, 0x10, 0xaa, 0x3f, 0x77, 0xa6, 0xd0, 0x57, 0x50, 0x53, 0xfc, 0x92, 0x6e, 0xea, 0x7e, 0x23, 0x7d, 0xf2, 0x89},
        {0x84, 0x8a, 0xf9, 0xf5, 0x7e, 0xb1, 0xa6, 0x16, 0xe2, 0xc3, 0x42, 0xc8, 0xce, 0xa5, 0x28, 0xb8, 0xa9, 0x5a, 0x5d, 0x16, 0xd9, 0xd8, 0x7b, 0xe9, 0xbb, 0x37, 0x84, 0xd0, 0xc3, 0x51, 0xc3, 0x2b},
        {0xc0, 0x43, 0x5c, 0xc3, 0x65, 0x4f, 0xb8, 0x5d, 0xd9, 0x33, 0x5b, 0xa9, 0x1a, 0xc3, 0xdb, 0xde, 0x1f, 0x85, 0xd5, 0x67, 0xd7, 0xad, 0x16, 0xf9, 0xde, 0x6e, 0x00, 0x9b, 0xca, 0x3f, 0x95, 0xb5},
        {0x92, 0x75, 0x47, 0xfe, 0x5e, 0x5e, 0x45, 0xe2, 0xfe, 0x99, 0xf1, 0x65, 0x1e, 0xa1, 0xcb, 0xf0, 0x97, 0xdc, 0x3a, 0x3d, 0x40, 0xdd, 0xd2, 0x1c, 0xee, 0x26, 0x05, 0x43, 0xc2, 0x88, 0xec, 0x6b},
        {0xc1, 0x17, 0xa3, 0x77, 0x0d, 0x3a, 0x34, 0x46, 0x9d, 0x50, 0xdf, 0xa7, 0xdb, 0x02, 0x03, 0x00, 0xd3, 0x06, 0xa3, 0x65, 0x37, 0x4f, 0xa8, 0x28, 0xc8, 0xb7, 0x80, 0xee, 0x1b, 0x9d, 0x7a, 0x34},
        {0x8f, 0xf2, 0x17, 0x8a, 0xe2, 0xdb, 0xe5, 0xe8, 0x72, 0xfa, 0xc7, 0x89, 0xa3, 0x4b, 0xc2, 0x28, 0xde, 0xbf, 0x54, 0xa8, 0x82, 0x74, 0x3c, 0xaa, 0xd1, 0x4f, 0x3a, 0x55, 0x0f, 0xdb, 0xe6, 0x8f},
        {0xab, 0xd0, 0x6c, 0x52, 0xed, 0x58, 0xff, 0x09, 0x12, 0x05, 0xd0, 0xf6, 0x27, 0x57, 0x4c, 0x8c, 0xbc, 0x1f, 0xe7, 0xcf, 0x79, 0x21, 0x0f, 0x5a, 0x22, 0x86, 0xf6, 0xe2, 0x3a, 0x27, 0xef, 0xa0},
        {0x63, 0x1f, 0x4a, 0xcb, 0x8d, 0x3c, 0xa4, 0x25, 0x3e, 0x30, 0x18, 0x49, 0xf1, 0x57, 0x57, 0x1d, 0x32, 0x11, 0xb6, 0xc1, 0x04, 0x53, 0x47, 0xbe, 0xfb, 0x7c, 0x77, 0xdf, 0x3c, 0x6c, 0xa7, 0xbd},
        {0xae, 0x88, 0xf2, 0x34, 0x2c, 0x23, 0x34, 0x45, 0x90, 0xbe, 0x20, 0x14, 0xfa, 0xb4, 0xf1, 0x79, 0xfd, 0x4b, 0xf7, 0xc9, 0x0d, 0xb1, 0x4f, 0xa4, 0x01, 0x8f, 0xcc, 0xe6, 0x89, 0xd2, 0x12, 0x7b},
        {0x93, 0xb8, 0x93, 0x85, 0x54, 0x6d, 0x71, 0x37, 0x9f, 0xe4, 0x1c, 0x39, 0xbc, 0x60, 0x2e, 0x8b, 0x7c, 0x8b, 0x2f, 0x78, 0xee, 0x91, 0x4d, 0x1f, 0x0a, 0xf0, 0xd4, 0x37, 0xa1, 0x89, 0xa8, 0xa4},
        {0x1d, 0x1e, 0x03, 0x6a, 0xbe, 0xef, 0x3f, 0x44, 0x84, 0x8c, 0xd7, 0x6e, 0xf6, 0xba, 0xa8, 0x89, 0xfc, 0xec, 0x56, 0xcd, 0x79, 0x67, 0xeb, 0x90, 0x9a, 0x46, 0x4b, 0xfc, 0x23, 0xc7, 0x24, 0x35},
        {0xa8, 0xe4, 0xed, 0xe4, 0xc5, 0xfe, 0x5e, 0x88, 0xd4, 0xfb, 0x19, 0x2e, 0x0a, 0x08, 0x21, 0xe9, 0x35, 0xba, 0x14, 0x5b, 0xbf, 0xc5, 0x9c, 0x25, 0x08, 0x28, 0x27, 0x55, 0xa5, 0xdf, 0x53, 0xa5},
        {0x8e, 0x4e, 0x37, 0xa3, 0xb9, 0x70, 0xf0, 0x79, 0xae, 0x9d, 0x22, 0xa4, 0x99, 0xa7, 0x14, 0xc8, 0x75, 0x76, 0x02, 0x73, 0xf7, 0x4a, 0x93, 0x98, 0x99, 0x5d, 0x32, 0xc0, 0x50, 0x27, 0xd8, 0x10},
        {0x61, 0xcf, 0xa4, 0x27, 0x92, 0xf9, 0x3b, 0x9f, 0xde, 0x36, 0xeb, 0x16, 0x3e, 0x97, 0x87, 0x09, 0xfa, 0xfa, 0x76, 0x16, 0xec, 0x3c, 0x7d, 0xad, 0x01, 0x35, 0x80, 0x6c, 0x3d, 0x91, 0xa2, 0x1b},
        {0xf0, 0x37, 0xc5, 0xd9, 0x16, 0x23, 0x28, 0x8b, 0x7d, 0x03, 0x02, 0xc1, 0xb9, 0x41, 0xb7, 0x26, 0x76, 0xa9, 0x43, 0xb3, 0x72, 0x65, 0x9d, 0xcd, 0x7d, 0x6e, 0xf4, 0x08, 0xa1, 0x1b, 0x40, 0xc0},
        {0x2a, 0x30, 0x63, 0x54, 0xca, 0x3e, 0xa9, 0x0b, 0x0e, 0x97, 0xea, 0xeb, 0xce, 0xa0, 0xa6, 0xd7, 0xc6, 0x52, 0x23, 0x99, 0xe8, 0x85, 0xc6, 0x13, 0xde, 0x82, 0x49, 0x22, 0xc8, 0x92, 0xc4, 0x90},
        {0x3c, 0xa6, 0xcd, 0xd7, 0x88, 0xa5, 0xbd, 0xc5, 0xef, 0x2d, 0xce, 0xeb, 0x16, 0xbc, 0xa3, 0x1e, 0x0a, 0x0d, 0x2c, 0x7e, 0x99, 0x21, 0xb6, 0xf7, 0x1d, 0x33, 0xe2, 0x5d, 0xd2, 0xf3, 0xcf, 0x53},
        {0xf7, 0x25, 0x78, 0x72, 0x1d, 0xb5, 0x6b, 0xf8, 0xf4, 0x95, 0x38, 0xb0, 0xae, 0x6e, 0xa4, 0x70, 0xc2, 0xfb, 0x13, 0x39, 0xdd, 0x26, 0x33, 0x3f, 0x13, 0x5f, 0x7d, 0xef, 0x45, 0x37, 0x6e, 0xc0},
        {0xe4, 0x49, 0xa0, 0x3e, 0xab, 0x35, 0x9e, 0x34, 0x09, 0x5f, 0x8b, 0x4b, 0x55, 0xcd, 0x7a, 0xc7, 0xc0, 0xec, 0x65, 0x10, 0xf2, 0xc4, 0xcc, 0x79, 0xfa, 0x6b, 0x1f, 0xee, 0x6b, 0x18, 0xc5, 0x9e},
        {0x73, 0xbd, 0x69, 0x78, 0xc5, 0x9f, 0x2b, 0x21, 0x94, 0x49, 0xb3, 0x67, 0x70, 0xfb, 0x31, 0x3f, 0xbe, 0x2d, 0xa2, 0x8f, 0x6b, 0x04, 0x27, 0x5f, 0x07, 0x1a, 0x1b, 0x19, 0x3d, 0xde, 0x20, 0x72},
        {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}
    };

#pragma HLS INLINE
#pragma HLS ARRAY_RESHAPE variable=roundconstant complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[0] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[1] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[2] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[3] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[4] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[5] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[6] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[7] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[8] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[9] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[10] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[11] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[12] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[13] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[14] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[15] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[16] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[17] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[18] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[19] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[20] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[21] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[22] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[23] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[24] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[25] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[26] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[27] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[28] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[29] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[30] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[31] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[32] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[33] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[34] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[35] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[36] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[37] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[38] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[39] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[40] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[41] complete dim=1
#pragma HLS ARRAY_RESHAPE variable=rc_rom[42] complete dim=1
#pragma HLS RESOURCE variable=rc_rom core=ROM_1P_1S

  int i;

  for (i = 0; i < 32; i++)
  {
#pragma HLS UNROLL
    roundconstant[i] = rc_rom[round][i];
  }
}

void jh(uint8 data[64], uint8 output[32], uint1 firstBlock, uint1 lastBlock)
{
#pragma HLS INTERFACE ap_hs port=output
  int i, j;
  uint8 round;
  static uint4 state[256];
  static uint4 stateTmp[256];
  static uint8 hash[128] = {
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0
  };
  uint8 hashTmp[128];

  const uint8 hashIV[128] = {
    0xEB, 0x98, 0xA3, 0x41, 0x2C, 0x20, 0xD3, 0xEB, 0x92, 0xCD, 0xBE, 0x7B, 0x9C, 0xB2, 0x45, 0xC1,
    0x1C, 0x93, 0x51, 0x91, 0x60, 0xD4, 0xC7, 0xFA, 0x26, 0x00, 0x82, 0xD6, 0x7E, 0x50, 0x8A, 0x03,
    0xA4, 0x23, 0x9E, 0x26, 0x77, 0x26, 0xB9, 0x45, 0xE0, 0xFB, 0x1A, 0x48, 0xD4, 0x1A, 0x94, 0x77,
    0xCD, 0xB5, 0xAB, 0x26, 0x02, 0x6B, 0x17, 0x7A, 0x56, 0xF0, 0x24, 0x42, 0x0F, 0xFF, 0x2F, 0xA8,
    0x71, 0xA3, 0x96, 0x89, 0x7F, 0x2E, 0x4D, 0x75, 0x1D, 0x14, 0x49, 0x08, 0xF7, 0x7D, 0xE2, 0x62,
    0x27, 0x76, 0x95, 0xF7, 0x76, 0x24, 0x8F, 0x94, 0x87, 0xD5, 0xB6, 0x57, 0x47, 0x80, 0x29, 0x6C,
    0x5C, 0x5E, 0x27, 0x2D, 0xAC, 0x8E, 0x0D, 0x6C, 0x51, 0x84, 0x50, 0xC6, 0x57, 0x05, 0x7A, 0x0F,
    0x7B, 0xE4, 0xD3, 0x67, 0x70, 0x24, 0x12, 0xEA, 0x89, 0xE3, 0xAB, 0x13, 0xD3, 0x1C, 0xD7, 0x69
  };

  static uint8 roundconstant[32];
  uint8 roundconstantTmp[32];

#pragma HLS ARRAY_RESHAPE variable=data complete dim=1
#pragma HLS ARRAY_RESHAPE variable=output complete dim=1
#pragma HLS ARRAY_RESHAPE variable=state complete dim=1
#pragma HLS ARRAY_RESHAPE variable=stateTmp complete dim=1
#pragma HLS ARRAY_RESHAPE variable=hash complete dim=1
#pragma HLS ARRAY_RESHAPE variable=hashIV complete dim=1
#pragma HLS ARRAY_RESHAPE variable=hashTmp complete dim=1
#pragma HLS ARRAY_RESHAPE variable=roundconstant complete dim=1
#pragma HLS ARRAY_RESHAPE variable=roundconstantTmp complete dim=1

#if DEBUG
  printf("--Hash State\n");
  if (firstBlock == 1)
    printHash(hashIV);
  else
    printHash(hash);
#endif

  /* State ^ Data */\
  if (firstBlock == 1)  
  {
    for (i = 0; i < 64; i++)
    {
#pragma HLS UNROLL
      hashTmp[i] = data[i] ^ hashIV[i];
    }
    for (i = 64; i < 128; i++)
    {
#pragma HLS UNROLL
      hashTmp[i] = hashIV[i];
    }
  }
  else
  {
    for (i = 0; i < 64; i++)
    {
#pragma HLS UNROLL
      hashTmp[i] = data[i] ^ hash[i];
    }
    for (i = 64; i < 128; i++)
    {
#pragma HLS UNROLL
      hashTmp[i] = hash[i];
    }    
  }
  
#if DEBUG
    printf("--Before grouping\n");
    printHash(hashTmp);
#endif

  E8_initialgroup(hashTmp, state);
  
#if DEBUG
    printf("--After grouping ===\n");
    printState(state);
#endif


  roundconstant[0] = 0x6a;
  roundconstant[1] = 0x09;
  roundconstant[2] = 0xe6;
  roundconstant[3] = 0x67;
  roundconstant[4] = 0xf3;
  roundconstant[5] = 0xbc;
  roundconstant[6] = 0xc9;
  roundconstant[7] = 0x08;
  roundconstant[8] = 0xb2;
  roundconstant[9] = 0xfb;
  roundconstant[10] = 0x13; 
  roundconstant[11] = 0x66;
  roundconstant[12] = 0xea;
  roundconstant[13] = 0x95;
  roundconstant[14] = 0x7d;
  roundconstant[15] = 0x3e;
  roundconstant[16] = 0x3a;
  roundconstant[17] = 0xde;
  roundconstant[18] = 0xc1;
  roundconstant[19] = 0x75;
  roundconstant[20] = 0x12;
  roundconstant[21] = 0x77;
  roundconstant[22] = 0x50;
  roundconstant[23] = 0x99;
  roundconstant[24] = 0xda;
  roundconstant[25] = 0x2f;
  roundconstant[26] = 0x59;
  roundconstant[27] = 0x0b;
  roundconstant[28] = 0x06;
  roundconstant[29] = 0x67;
  roundconstant[30] = 0x32;
  roundconstant[31] = 0x2a;  

  /* Main round */
  for(round = 0; round < NB_ROUNDS; round++)
  {
#if DEBUG_ROUND
  printf("Round - %d\n", round);
#endif
    R8(state, roundconstant, stateTmp);
    getRoundConstant(round, roundconstantTmp);

    for (i = 0; i < 256; i++)
    {
#pragma HLS UNROLL
        roundconstant[i] = roundconstantTmp[i];
    }
    for (i = 0; i < 256; i++)
    {
#pragma HLS UNROLL
      state[i] = stateTmp[i];
    }
  }

#if DEBUG
    printf("--After R8\n");
    printState(state);
#endif

  E8_finaldegroup(state, hashTmp);

#if DEBUG
    printf("--After degrouping\n");
    printHash(hashTmp);
#endif

  /*final swap Phi_8*/
  for (i = 64; i < 128; i++)
  {
#pragma HLS UNROLL
    hashTmp[i] = data[i-64] ^ hashTmp[i];
  }

  /* Output data and new hash value */
  for (i = 0; i < 128; i++)
  {
#pragma HLS UNROLL
    hash[i] = hashTmp[i];
  }
  
#if DEBUG
    printf("--After final XOR\n");
    printHash(hash);
#endif

  if (lastBlock == 1)
    for (i = 96; i < 128; i++)
    {
  #pragma HLS UNROLL
      output[i-96] = hashTmp[i];
    }
}
