// ap_fixed testbench. Same scheme as the float baseline (no
// input.data/check.data; check_data() in the original local_support.cpp is
// a stub): deterministic synthetic inputs run through workload() and
// checked against an independently-computed reference. work_mem and
// cost_of_opening_x are continuous -> allclose; switch_membership is
// discrete -> exact match.
#include <cmath>
#include <cstdio>
#include <cstring>

#include "fpx_check.h"
#include "streamcluster.h"

extern "C" void workload(fixed_t coord[BATCH_SIZE * DIM], fixed_t weight[BATCH_SIZE],
                          fixed_t cost[BATCH_SIZE], fixed_t target[DIM],
                          int assign[BATCH_SIZE], int center_table[BATCH_SIZE],
                          char switch_membership[BATCH_SIZE],
                          fixed_t work_mem[MAX_WORK_MEM_SIZE], int num,
                          fixed_t cost_of_opening_x[1], int numcenter);

static const int NUMCENTER = MAX_WORK_MEM_SIZE;

int main() {
  static float coord_f[BATCH_SIZE * DIM];
  static float weight_f[BATCH_SIZE];
  static float cost_f[BATCH_SIZE];
  static float target_f[DIM];
  static int assign[BATCH_SIZE];
  static int center_table[BATCH_SIZE];

  static fixed_t coord[BATCH_SIZE * DIM];
  static fixed_t weight[BATCH_SIZE];
  static fixed_t cost[BATCH_SIZE];
  static fixed_t target[DIM];
  static char switch_membership[BATCH_SIZE] = {};
  static fixed_t work_mem[NUMCENTER] = {};
  static char switch_membership_ref[BATCH_SIZE] = {};
  static float work_mem_ref[NUMCENTER] = {};
  fixed_t cost_of_opening_x = 0;
  float cost_of_opening_x_ref = 0.0f;

  for (int i = 0; i < BATCH_SIZE * DIM; i++) coord_f[i] = sinf(i * 0.001f) * 10.0f;
  for (int i = 0; i < BATCH_SIZE; i++) weight_f[i] = 1.0f;
  for (int i = 0; i < BATCH_SIZE; i++) cost_f[i] = fabsf(cosf(i * 0.01f)) * 5.0f;
  for (int j = 0; j < DIM; j++) target_f[j] = cosf(j * 0.01f) * 10.0f;
  for (int i = 0; i < BATCH_SIZE; i++) assign[i] = i % BATCH_SIZE;
  for (int i = 0; i < BATCH_SIZE; i++) center_table[i] = i % NUMCENTER;

  for (int i = 0; i < BATCH_SIZE * DIM; i++) coord[i] = coord_f[i];
  for (int i = 0; i < BATCH_SIZE; i++) weight[i] = weight_f[i];
  for (int i = 0; i < BATCH_SIZE; i++) cost[i] = cost_f[i];
  for (int j = 0; j < DIM; j++) target[j] = target_f[j];

  workload(coord, weight, cost, target, assign, center_table, switch_membership,
           work_mem, BATCH_SIZE, &cost_of_opening_x, NUMCENTER);

  for (int i = 0; i < BATCH_SIZE; i++) {
    float sum = 0;
    for (int j = 0; j < DIM; j++) {
      float a = coord_f[i * DIM + j] - target_f[j];
      sum += a * a;
    }
    float current_cost = sum * weight_f[i] - cost_f[i];
    int local_center_index = center_table[assign[i]];
    if (current_cost < 0) {
      switch_membership_ref[i] = 1;
      cost_of_opening_x_ref += current_cost;
    } else {
      work_mem_ref[local_center_index] -= current_cost;
    }
  }

  bool switch_ok = memcmp(switch_membership, switch_membership_ref, sizeof(switch_membership)) == 0;

  fpx_check::ArrayChecker work_mem_checker("work_mem");
  for (int i = 0; i < NUMCENTER; i++)
    work_mem_checker.add((double)(float)work_mem[i], (double)work_mem_ref[i]);

  fpx_check::ArrayChecker cost_checker("cost_of_opening_x");
  cost_checker.add((double)(float)cost_of_opening_x, (double)cost_of_opening_x_ref);

  bool pass = switch_ok && work_mem_checker.passed() && cost_checker.passed();
  printf("switch_membership exact match: %s\n", switch_ok ? "yes" : "no");
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
