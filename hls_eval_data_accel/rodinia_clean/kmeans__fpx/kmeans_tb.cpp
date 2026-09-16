// ap_fixed testbench. Same scheme as the float baseline (this design's own
// local_support.cpp doesn't read input.data/check.data): generate
// deterministic random inputs, run through workload(), and check against an
// independently-computed nearest-cluster reference. Membership is a
// discrete (argmin) decision, so this reports mismatch count directly
// rather than using an allclose-style tolerance.
#include <cstdio>
#include <cstdlib>

#include "kmeans.h"

extern "C" void workload(fixed_t feature[NPOINTS * NFEATURES],
                          fixed_t clusters[NCLUSTERS * NFEATURES],
                          int membership[NPOINTS]);

static float *FEATURE_F, *CLUSTER_F;
static fixed_t *FEATURE, *CLUSTER;
static int *MEMBERSHIP;

int main() {
  FEATURE_F = new float[NPOINTS * NFEATURES];
  CLUSTER_F = new float[NCLUSTERS * NFEATURES];
  FEATURE = new fixed_t[NPOINTS * NFEATURES];
  CLUSTER = new fixed_t[NCLUSTERS * NFEATURES];
  MEMBERSHIP = new int[NPOINTS];

  const float low = -10.0f, high = 10.0f;
  for (int i = 0; i < NPOINTS * NFEATURES; ++i)
    FEATURE_F[i] = low + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / (high - low)));
  for (int i = 0; i < NCLUSTERS * NFEATURES; ++i)
    CLUSTER_F[i] = low + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / (high - low)));

  for (int i = 0; i < NPOINTS * NFEATURES; ++i) FEATURE[i] = FEATURE_F[i];
  for (int i = 0; i < NCLUSTERS * NFEATURES; ++i) CLUSTER[i] = CLUSTER_F[i];

  workload(FEATURE, CLUSTER, MEMBERSHIP);

  int errors = 0;
  for (int i = 0; i < NPOINTS; i++) {
    float min_dist = FLT_MAX;
    int index = 0;
    for (int j = 0; j < NCLUSTERS; j++) {
      float dist = 0.0f;
      for (int k = 0; k < NFEATURES; k++) {
        float diff = FEATURE_F[NFEATURES * i + k] - CLUSTER_F[NFEATURES * j + k];
        dist += diff * diff;
      }
      if (dist < min_dist) { min_dist = dist; index = j; }
    }
    if (index != MEMBERSHIP[i]) errors++;
  }

  bool pass = errors == 0;
  printf("mismatches=%d/%d\n", errors, NPOINTS);
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
