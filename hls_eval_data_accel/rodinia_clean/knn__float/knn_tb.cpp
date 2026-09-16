// Minimal software testbench. This design's own local_support.cpp doesn't
// read input.data/check.data either: it generates a deterministic input
// (i+1.0 pattern) and checks against an independently-computed squared-
// distance reference, so this testbench reproduces that scheme directly.
#include <cstdio>

#include "knn.h"

extern "C" void workload(float inputQuery[NUM_FEATURE],
                          float searchSpace[NUM_PT_IN_SEARCHSPACE * NUM_FEATURE],
                          float distance[NUM_PT_IN_SEARCHSPACE]);

static float input_query[NUM_FEATURE];
static float *search_space_data;
static float *distance;
static float *distance_ref;

int main() {
  search_space_data = new float[NUM_PT_IN_SEARCHSPACE * NUM_FEATURE];
  distance = new float[NUM_PT_IN_SEARCHSPACE];
  distance_ref = new float[NUM_PT_IN_SEARCHSPACE];

  for (int i = 0; i < NUM_FEATURE; ++i) input_query[i] = i + 1.0f;
  for (int i = 0; i < NUM_PT_IN_SEARCHSPACE * NUM_FEATURE; ++i)
    search_space_data[i] = i + 1.0f;

  workload(input_query, search_space_data, distance);

  for (int i = 0; i < NUM_PT_IN_SEARCHSPACE; i++) {
    float sum = 0.0f;
    for (int j = 0; j < NUM_FEATURE; ++j) {
      float delta = search_space_data[i * NUM_FEATURE + j] - input_query[j];
      sum += delta * delta;
    }
    distance_ref[i] = sum;
  }

  int errors = 0;
  for (int i = 0; i < NUM_PT_IN_SEARCHSPACE; i++)
    if (distance[i] != distance_ref[i]) errors++;

  bool pass = errors == 0;
  printf(pass ? "PASS\n" : "FAIL (%d errors)\n", errors);
  return pass ? 0 : 1;
}
