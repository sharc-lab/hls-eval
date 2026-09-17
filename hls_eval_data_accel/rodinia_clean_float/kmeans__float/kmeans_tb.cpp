// Minimal software testbench. This design's own local_support.cpp doesn't
// read input.data/check.data at all: it generates random inputs and checks
// the result against an independently-computed nearest-cluster reference,
// so this testbench reproduces that exact scheme self-contained.
#include <cstdio>
#include <cstdlib>

#include "kmeans.h"

extern "C" void workload(float feature[NPOINTS * NFEATURES],
                          float clusters[NCLUSTERS * NFEATURES],
                          int membership[NPOINTS]);

static float *FEATURE, *CLUSTER;
static int *MEMBERSHIP;

int main() {
  FEATURE = new float[NPOINTS * NFEATURES];
  CLUSTER = new float[NCLUSTERS * NFEATURES];
  MEMBERSHIP = new int[NPOINTS];

  const float low = -10.0f, high = 10.0f;
  for (int i = 0; i < NPOINTS * NFEATURES; ++i)
    FEATURE[i] = low + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / (high - low)));
  for (int i = 0; i < NCLUSTERS * NFEATURES; ++i)
    CLUSTER[i] = low + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / (high - low)));

  workload(FEATURE, CLUSTER, MEMBERSHIP);

  int errors = 0;
  for (int i = 0; i < NPOINTS; i++) {
    float min_dist = FLT_MAX;
    int index = 0;
    for (int j = 0; j < NCLUSTERS; j++) {
      float dist = 0.0f;
      for (int k = 0; k < NFEATURES; k++) {
        float diff = FEATURE[NFEATURES * i + k] - CLUSTER[NFEATURES * j + k];
        dist += diff * diff;
      }
      if (dist < min_dist) { min_dist = dist; index = j; }
    }
    if (index != MEMBERSHIP[i]) errors++;
  }

  bool pass = errors == 0;
  printf(pass ? "PASS\n" : "FAIL (%d errors)\n", errors);
  return pass ? 0 : 1;
}
