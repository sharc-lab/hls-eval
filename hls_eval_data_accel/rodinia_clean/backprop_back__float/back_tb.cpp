// Minimal software testbench. The original local_support.cpp's check_data()
// is a stub that always returns "correct" (no real reference), so this
// testbench provides a genuine one: deterministic synthetic inputs, run
// through workload(), and checked against the same weight-update formula
// (delta-rule with momentum) computed independently here.
#include <cmath>
#include <cstdio>
#include <cstring>

#include "backprop.h"

extern "C" void workload(float delta[17], float ly[65537], float w[65537 * 17],
                          float oldw[65537 * 17]);

int main() {
  static float delta[17];
  static float ly[65537];
  float *w = new float[65537 * 17];
  float *oldw = new float[65537 * 17];
  float *w_ref = new float[65537 * 17];
  float *oldw_ref = new float[65537 * 17];

  for (int j = 0; j < 17; j++) delta[j] = sinf(j * 0.37f);
  for (int k = 0; k < 65537; k++) ly[k] = cosf(k * 0.001f);
  for (int i = 0; i < 65537 * 17; i++) {
    w[i] = w_ref[i] = sinf(i * 0.0001f) * 0.5f;
    oldw[i] = oldw_ref[i] = cosf(i * 0.0002f) * 0.3f;
  }

  workload(delta, ly, w, oldw);

  float ly0 = 1.0f;
  for (int j = 1; j <= 16; j++) {
    for (int k = 0; k <= 65536; k++) {
      float lyk = (k == 0) ? ly0 : ly[k];
      float new_dw = (ETA * delta[j] * lyk) + (MOMENTUM * oldw_ref[k * 17 + j]);
      w_ref[k * 17 + j] += new_dw;
      oldw_ref[k * 17 + j] = new_dw;
    }
  }

  bool pass = memcmp(w, w_ref, sizeof(float) * 65537 * 17) == 0 &&
              memcmp(oldw, oldw_ref, sizeof(float) * 65537 * 17) == 0;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
