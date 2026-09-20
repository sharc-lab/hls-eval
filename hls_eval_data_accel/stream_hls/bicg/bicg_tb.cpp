//===------------------------------------------------------------*- C++ -*-===//
// Testbench for the `bicg` StreamHLS design.
//
// Loads the input tensors and the golden output tensors (`*.bin`, raw
// row-major float32, located in the working directory), runs `forward`, and
// compares every output element against the golden value numpy.allclose
// style: |actual - expected| <= atol + rtol * |expected|. Mean absolute error
// (MAE) and mean relative error (MRE) are also reported for diagnostics.
//===----------------------------------------------------------------------===//
#include <cmath>
#include <cstddef>
#include <cstdio>
#include <fstream>

void forward(
  float[410][390],
  float[410][390],
  float[410],
  float[390],
  float[390],
  float[410]
);

namespace {

constexpr double kAtol = 0.001;
constexpr double kRtol = 0.01;
constexpr size_t kMaxReportedMismatches = 20;

bool load_bin(const char *path, float *dst, size_t count) {
  std::ifstream ifs(path, std::ios::binary);
  if (!ifs.is_open()) {
    fprintf(stderr, "cannot open file %s\n", path);
    return false;
  }
  ifs.read(reinterpret_cast<char *>(dst), count * sizeof(float));
  if (static_cast<size_t>(ifs.gcount()) != count * sizeof(float)) {
    fprintf(stderr, "file %s is too short (expected %zu floats)\n", path, count);
    return false;
  }
  return true;
}

bool check_output(const char *name, const float *actual, const float *golden,
                  size_t count) {
  size_t mismatches = 0;
  double abs_error_sum = 0.0, rel_error_sum = 0.0;
  for (size_t i = 0; i < count; i++) {
    const double a = actual[i], e = golden[i];
    const double abs_error = std::fabs(a - e);
    const double abs_expected = std::fabs(e);
    const double tolerance = kAtol + kRtol * abs_expected;
    abs_error_sum += abs_error;
    rel_error_sum += abs_error / (abs_expected > 1e-6 ? abs_expected : 1e-6);
    // written so that NaN in the actual output counts as a mismatch
    if (!(abs_error <= tolerance)) {
      if (++mismatches <= kMaxReportedMismatches)
        fprintf(stderr,
                "%s[%zu] mismatch: actual=%.9g expected=%.9g abs_error=%.9g "
                "tolerance=%.9g\n",
                name, i, a, e, abs_error, tolerance);
    }
  }
  fprintf(stderr,
          "%s: MAE=%.9g MRE=%.9g mismatches=%zu/%zu (atol=%.3g rtol=%.3g)\n",
          name, abs_error_sum / count, rel_error_sum / count, mismatches, count,
          kAtol, kRtol);
  return mismatches == 0;
}

}  // namespace

int main() {
  static float v0[410][390];  // input
  static float v1[410][390];  // input
  static float v2[410];  // input
  static float v3[390];  // input
  static float v4[390];  // output
  static float v5[410];  // output
  static float golden_0[390];
  static float golden_1[410];

  if (!load_bin("input_0.bin", reinterpret_cast<float *>(v0), 159900)) return 1;
  if (!load_bin("input_1.bin", reinterpret_cast<float *>(v1), 159900)) return 1;
  if (!load_bin("input_2.bin", reinterpret_cast<float *>(v2), 410)) return 1;
  if (!load_bin("input_3.bin", reinterpret_cast<float *>(v3), 390)) return 1;
  if (!load_bin("output_0.bin", reinterpret_cast<float *>(golden_0), 390)) return 1;
  if (!load_bin("output_1.bin", reinterpret_cast<float *>(golden_1), 410)) return 1;

  forward(v0, v1, v2, v3, v4, v5);

  bool pass = true;
  pass &= check_output("output_0", reinterpret_cast<const float *>(v4), reinterpret_cast<const float *>(golden_0), 390);
  pass &= check_output("output_1", reinterpret_cast<const float *>(v5), reinterpret_cast<const float *>(golden_1), 410);

  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
