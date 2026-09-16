// Minimal software testbench. workload() here is the "gain" evaluation
// step of the PAM/local-search k-median algorithm: a small, self-contained,
// purely combinational computation over one batch of points -- everything
// else in this design's original local_support.cpp (streamCluster/pkmedian/
// pgain, ~800 lines) is CPU-side clustering orchestration around it, with
// no independent correctness check at all (its check_data() is a stub that
// always returns "correct"). So this testbench exercises workload() itself
// directly: deterministic synthetic inputs, run through workload(), and
// checked against the same gain formula computed independently here.
#include <cmath>
#include <cstdio>
#include <cstring>

#include "streamcluster.h"

extern "C" void workload(float coord[BATCH_SIZE * DIM], float weight[BATCH_SIZE],
                          float cost[BATCH_SIZE], float target[DIM],
                          int assign[BATCH_SIZE], int center_table[BATCH_SIZE],
                          char switch_membership[BATCH_SIZE],
                          float work_mem[MAX_WORK_MEM_SIZE], int num,
                          float cost_of_opening_x[1], int numcenter);

static const int NUMCENTER = MAX_WORK_MEM_SIZE;

int main() {
  static float coord[BATCH_SIZE * DIM];
  static float weight[BATCH_SIZE];
  static float cost[BATCH_SIZE];
  static float target[DIM];
  static int assign[BATCH_SIZE];
  static int center_table[BATCH_SIZE];
  static char switch_membership[BATCH_SIZE] = {};
  static float work_mem[NUMCENTER] = {};
  static char switch_membership_ref[BATCH_SIZE] = {};
  static float work_mem_ref[NUMCENTER] = {};
  float cost_of_opening_x = 0.0f;
  float cost_of_opening_x_ref = 0.0f;

  for (int i = 0; i < BATCH_SIZE * DIM; i++) coord[i] = sinf(i * 0.001f) * 10.0f;
  for (int i = 0; i < BATCH_SIZE; i++) weight[i] = 1.0f;
  for (int i = 0; i < BATCH_SIZE; i++) cost[i] = fabsf(cosf(i * 0.01f)) * 5.0f;
  for (int j = 0; j < DIM; j++) target[j] = cosf(j * 0.01f) * 10.0f;
  for (int i = 0; i < BATCH_SIZE; i++) assign[i] = i % BATCH_SIZE;
  for (int i = 0; i < BATCH_SIZE; i++) center_table[i] = i % NUMCENTER;

  workload(coord, weight, cost, target, assign, center_table, switch_membership,
           work_mem, BATCH_SIZE, &cost_of_opening_x, NUMCENTER);

  for (int i = 0; i < BATCH_SIZE; i++) {
    float sum = 0.0f;
    for (int j = 0; j < DIM; j++) {
      float a = coord[i * DIM + j] - target[j];
      sum += a * a;
    }
    float current_cost = sum * weight[i] - cost[i];
    int local_center_index = center_table[assign[i]];
    if (current_cost < 0) {
      switch_membership_ref[i] = 1;
      cost_of_opening_x_ref += current_cost;
    } else {
      work_mem_ref[local_center_index] -= current_cost;
    }
  }

  bool pass = memcmp(switch_membership, switch_membership_ref, sizeof(switch_membership)) == 0 &&
              memcmp(work_mem, work_mem_ref, sizeof(work_mem)) == 0 &&
              cost_of_opening_x == cost_of_opening_x_ref;
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
