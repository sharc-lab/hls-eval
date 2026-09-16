// ap_fixed testbench. Same scheme as the float baseline (no
// input.data/check.data): deterministic synthetic inputs run through
// workload(), independently recomputed in float as ground truth, compared
// via fpx_check's numpy.allclose-style tolerance.
#include <cmath>
#include <cstdio>
#include <cstring>

#include "backprop.h"
#include "fpx_check.h"

extern "C" void workload(fixed_t delta[17], fixed_t ly[65537], fixed_t w[65537 * 17],
                          fixed_t oldw[65537 * 17]);

int main() {
  static fixed_t delta[17];
  static fixed_t ly[65537];
  fixed_t *w = new fixed_t[65537 * 17];
  fixed_t *oldw = new fixed_t[65537 * 17];
  float *w_ref = new float[65537 * 17];
  float *oldw_ref = new float[65537 * 17];

  for (int j = 0; j < 17; j++) delta[j] = sinf(j * 0.37f);
  for (int k = 0; k < 65537; k++) ly[k] = cosf(k * 0.001f);
  for (int i = 0; i < 65537 * 17; i++) {
    float wv = sinf(i * 0.0001f) * 0.5f;
    float owv = cosf(i * 0.0002f) * 0.3f;
    w[i] = wv;
    oldw[i] = owv;
    w_ref[i] = wv;
    oldw_ref[i] = owv;
  }

  workload(delta, ly, w, oldw);

  float ly0 = 1.0f;
  for (int j = 1; j <= 16; j++) {
    for (int k = 0; k <= 65536; k++) {
      float lyk = (k == 0) ? ly0 : cosf(k * 0.001f);
      float deltaj = sinf(j * 0.37f);
      float new_dw = (0.3f * deltaj * lyk) + (0.3f * oldw_ref[k * 17 + j]);
      w_ref[k * 17 + j] += new_dw;
      oldw_ref[k * 17 + j] = new_dw;
    }
  }

  fpx_check::ArrayChecker checker("w+oldw");
  for (int i = 0; i < 65537 * 17; i++)
    checker.add((double)(float)w[i], (double)w_ref[i]);
  for (int i = 0; i < 65537 * 17; i++)
    checker.add((double)(float)oldw[i], (double)oldw_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
