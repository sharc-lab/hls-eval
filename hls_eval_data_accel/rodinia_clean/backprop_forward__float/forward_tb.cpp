// Minimal software testbench. The original local_support.cpp's check_data()
// is a stub that always returns "correct" (no real reference), so this
// testbench provides a genuine one: deterministic synthetic inputs, run
// through workload(), and checked against the same forward-pass formula
// (weighted sum + sigmoid) computed independently here.
#include <cmath>
#include <cstdio>
#include <cstring>

#include "backprop.h"

extern "C" void workload(float l1[65537], float l2[17], float conn[65537 * 17]);

int main() {
  static float l1[65537];
  static float l2[17];
  static float l2_ref[17];
  float *conn = new float[65537 * 17];

  for (int k = 0; k < 65537; k++) l1[k] = cosf(k * 0.001f);
  for (int i = 0; i < 65537 * 17; i++) conn[i] = sinf(i * 0.0001f) * 0.5f;

  workload(l1, l2, conn);

  float l1_0 = 1.0f;
  for (int j = 1; j <= 16; j++) {
    float sum = 0.0f;
    for (int k = 0; k <= 65536; k++) {
      float l1k = (k == 0) ? l1_0 : l1[k];
      sum += conn[k * 17 + j] * l1k;
    }
    l2_ref[j] = 1.0f / (1.0f + expf(-sum));
  }

  bool pass = memcmp(l2, l2_ref, sizeof(float) * 17) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
