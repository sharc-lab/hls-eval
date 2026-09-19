/* Standalone reconstruction of Kyber's reference NTT (round-3 ref/ntt.c and
 * ref/reduce.c, montgomery_reduce only); see kernel_description.md.
 *
 * This file used to pull in params.h/ntt.h/reduce.h from the full Kyber
 * reference tree. Those headers declare the entire Kyber KEM (key sizes,
 * compression, the 90S/AES variant, a KYBER_NAMESPACE renaming macro for
 * linking multiple parameter sets together, ...); this kernel only ever
 * needs KYBER_Q and QINV. Everything below is that slice, folded in
 * directly with the unused rest dropped.
 */
#include <stdint.h>

#define KYBER_Q 3329
#define QINV   -3327 /* q^-1 mod 2^16 */

/*************************************************
* Name:        montgomery_reduce
*
* Description: Montgomery reduction; given a 32-bit integer a, computes
*              16-bit integer congruent to a * R^-1 mod q, where R=2^16
*
* Arguments:   - int32_t a: input integer to be reduced;
*                           has to be in {-q2^15,...,q2^15-1}
*
* Returns:     integer in {-q+1,...,q-1} congruent to a * R^-1 modulo q.
**************************************************/
int16_t montgomery_reduce(int32_t a)
{
  int16_t t;

  t = (int16_t)a*QINV;
  t = (a - (int32_t)t*KYBER_Q) >> 16;
  return t;
}

const int16_t zetas[128] = {
  -1044,  -758,  -359, -1517,  1493,  1422,   287,   202,
   -171,   622,  1577,   182,   962, -1202, -1474,  1468,
    573, -1325,   264,   383,  -829,  1458, -1602,  -130,
   -681,  1017,   732,   608, -1542,   411,  -205, -1571,
   1223,   652,  -552,  1015, -1293,  1491,  -282, -1544,
    516,    -8,  -320,  -666, -1618, -1162,   126,  1469,
   -853,   -90,  -271,   830,   107, -1421,  -247,  -951,
   -398,   961, -1508,  -725,   448, -1065,   677, -1275,
  -1103,   430,   555,   843, -1251,   871,  1550,   105,
    422,   587,   177,  -235,  -291,  -460,  1574,  1653,
   -246,   778,  1159,  -147,  -777,  1483,  -602,  1119,
  -1590,   644,  -872,   349,   418,   329,  -156,   -75,
    817,  1097,   603,   610,  1322, -1285, -1465,   384,
  -1215,  -136,  1218, -1335,  -874,   220, -1187, -1659,
  -1185, -1530, -1278,   794, -1510,  -854,  -870,   478,
   -108,  -308,   996,   991,   958, -1460,  1522,  1628
};

static int16_t fqmul(int16_t a, int16_t b) {
  return montgomery_reduce((int32_t)a*b);
}

/*************************************************
* Name:        ntt
*
* Description: Inplace number-theoretic transform (NTT) in Rq.
*              input is in standard order, output is in bitreversed order
*
* Arguments:   - int16_t r[256]: input/output vector of elements of Zq
**************************************************/
void ntt(int16_t r[256]) {
  int16_t t, zeta;

  /* See dilithium_ntt.c's ntt() for the rationale: the original nests loops
   * bounded by the loop-carried `len` (halving each stage: 128, 64, ..., 2),
   * which Vitis HLS's static trip-count analysis cannot resolve, so the
   * design's overall latency is reported as "undef". This form flattens the
   * `start`/`j` pair into a single loop over `stage_idx` in [0, 128), a
   * fixed 128 butterfly ops per stage regardless of `len`, recovering
   * `group`/`off` (the original `start`/`j - start`) via division/modulo
   * instead of using them as loop bounds. Verified equivalent to the
   * original control flow by exhaustive simulation.
   */
  for (unsigned int stage = 0; stage < 7; stage++) {
    unsigned int len = 128u >> stage;
    for (unsigned int stage_idx = 0; stage_idx < 128; stage_idx++) {
      unsigned int group = stage_idx / len;
      unsigned int off = stage_idx % len;
      unsigned int j = group * (2 * len) + off;
      zeta = zetas[(1u << stage) + group];
      t = fqmul(zeta, r[j + len]);
      r[j + len] = r[j] - t;
      r[j] = r[j] + t;
    }
  }
}

void kyber_ntt(int16_t a[256]) { ntt(a); }
