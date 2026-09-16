#pragma once
/*
 * numpy.allclose-style checker for the ap_fixed (__fpx) conversions of the
 * rodinia_clean float kernels: |actual - expected| <= atol + rtol*|expected|,
 * comparing the ap_fixed kernel output (cast to double) against the
 * existing float-precision check.data reference (also cast to double).
 * Mirrors hls_eval_check.h's ArrayChecker used for the polybench fixed
 * conversions.
 */
#include <cmath>
#include <cstdio>

namespace fpx_check {

constexpr double kAtol = 1e-2;
constexpr double kRtol = 1e-2;
constexpr size_t kMaxReportedMismatches = 20;

class ArrayChecker {
 public:
  explicit ArrayChecker(const char *name) : name_(name) {}

  void add(double actual, double expected) {
    const double abs_error = std::fabs(actual - expected);
    const double abs_expected = std::fabs(expected);
    const double tolerance = kAtol + kRtol * abs_expected;
    abs_error_sum_ += abs_error;
    rel_error_sum_ += abs_error / (abs_expected > 1e-6 ? abs_expected : 1e-6);
    ++count_;
    if (abs_error > tolerance) {
      ++mismatch_count_;
      if (mismatch_count_ <= kMaxReportedMismatches) {
        fprintf(stderr,
                "fpx_check: %s[%zu] mismatch: actual=%.9f expected=%.9f "
                "abs_error=%.9g tolerance=%.9g\n",
                name_, count_ - 1, actual, expected, abs_error, tolerance);
      }
    }
  }

  bool passed() const {
    const double mae = count_ ? abs_error_sum_ / count_ : 0.0;
    const double mre = count_ ? rel_error_sum_ / count_ : 0.0;
    fprintf(stderr,
            "fpx_check: %s MAE=%.9f MRE=%.9f mismatches=%zu/%zu "
            "(atol=%.3g rtol=%.3g)\n",
            name_, mae, mre, mismatch_count_, count_, kAtol, kRtol);
    return mismatch_count_ == 0;
  }

 private:
  const char *name_;
  double abs_error_sum_ = 0.0;
  double rel_error_sum_ = 0.0;
  size_t count_ = 0;
  size_t mismatch_count_ = 0;
};

}  // namespace fpx_check
