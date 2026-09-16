// ap_fixed testbench. Same scheme as the float baseline (no
// input.data/check.data): deterministic synthetic inputs run through
// workload(), independently recomputed in float as ground truth, compared
// via fpx_check's numpy.allclose-style tolerance.
#include <cmath>
#include <cstdio>
#include <cstring>

#include "ap_fixed.h"
typedef ap_fixed<32, 16> fixed_t;
#include "fpx_check.h"

extern "C" void workload(fixed_t l1[65537], fixed_t l2[17], fixed_t conn[65537 * 17]);

int main() {
  static fixed_t l1[65537];
  static fixed_t l2[17];
  static float l2_ref[17];
  fixed_t *conn = new fixed_t[65537 * 17];

  for (int k = 0; k < 65537; k++) l1[k] = cosf(k * 0.001f);
  for (int i = 0; i < 65537 * 17; i++) conn[i] = sinf(i * 0.0001f) * 0.5f;

  workload(l1, l2, conn);

  float l1_0 = 1.0f;
  for (int j = 1; j <= 16; j++) {
    float sum = 0.0f;
    for (int k = 0; k <= 65536; k++) {
      float l1k = (k == 0) ? l1_0 : cosf(k * 0.001f);
      float connk = sinf((k * 17 + j) * 0.0001f) * 0.5f;
      sum += connk * l1k;
    }
    l2_ref[j] = 1.0f / (1.0f + expf(-sum));
  }

  fpx_check::ArrayChecker checker("l2");
  for (int j = 1; j <= 16; j++)
    checker.add((double)(float)l2[j], (double)l2_ref[j]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
