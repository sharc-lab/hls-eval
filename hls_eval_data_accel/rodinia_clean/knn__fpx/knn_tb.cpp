// ap_fixed testbench. Same scheme as the float baseline (this design's own
// local_support.cpp doesn't read input.data/check.data): generate a
// deterministic input, run through workload(), and check against an
// independently-computed squared-distance reference via fpx_check's
// numpy.allclose-style tolerance.
#include <cstdio>

#include "fpx_check.h"
#include "knn.h"

extern "C" void workload(fixed_t inputQuery[NUM_FEATURE],
                          fixed_t searchSpace[NUM_PT_IN_SEARCHSPACE * NUM_FEATURE],
                          fixed_t distance[NUM_PT_IN_SEARCHSPACE]);

static float input_query_f[NUM_FEATURE];
static float *search_space_data_f;
static float *distance_ref;

static fixed_t input_query[NUM_FEATURE];
static fixed_t *search_space_data;
static fixed_t *distance;

int main() {
  search_space_data_f = new float[NUM_PT_IN_SEARCHSPACE * NUM_FEATURE];
  distance_ref = new float[NUM_PT_IN_SEARCHSPACE];
  search_space_data = new fixed_t[NUM_PT_IN_SEARCHSPACE * NUM_FEATURE];
  distance = new fixed_t[NUM_PT_IN_SEARCHSPACE];

  // The float baseline uses i+1.0 (growing to ~2e6), whose squared deltas
  // would badly overflow ap_fixed<32,16>'s ~+-32767 range -- that overflow
  // is an artifact of this synthetic test data's unbounded range, not of
  // the kernel's arithmetic, so bound it to a representable range instead.
  for (int i = 0; i < NUM_FEATURE; ++i) input_query_f[i] = (i % 100) + 1.0f;
  for (int i = 0; i < NUM_PT_IN_SEARCHSPACE * NUM_FEATURE; ++i)
    search_space_data_f[i] = (i % 100) + 1.0f;

  for (int i = 0; i < NUM_FEATURE; ++i) input_query[i] = input_query_f[i];
  for (int i = 0; i < NUM_PT_IN_SEARCHSPACE * NUM_FEATURE; ++i)
    search_space_data[i] = search_space_data_f[i];

  workload(input_query, search_space_data, distance);

  for (int i = 0; i < NUM_PT_IN_SEARCHSPACE; i++) {
    float sum = 0.0f;
    for (int j = 0; j < NUM_FEATURE; ++j) {
      float delta = search_space_data_f[i * NUM_FEATURE + j] - input_query_f[j];
      sum += delta * delta;
    }
    distance_ref[i] = sum;
  }

  fpx_check::ArrayChecker checker("distance");
  for (int i = 0; i < NUM_PT_IN_SEARCHSPACE; i++)
    checker.add((double)(float)distance[i], (double)distance_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
