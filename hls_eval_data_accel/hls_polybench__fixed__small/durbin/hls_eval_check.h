#pragma once
// Shared correctness-check helpers for the polybench fixed-point testbenches:
// load the float golden reference dumped in tb_data.txt and compare it
// against the fixed-point kernel output element-by-element, numpy.allclose
// style: |actual - expected| <= atol + rtol * |expected|. Aggregate mean
// absolute error (MAE) and mean relative error (MRE) are also reported for
// diagnostics.

#include <cctype>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace hls_eval_check {

constexpr double kAtol = 1e-2;
constexpr double kRtol = 1e-2;
constexpr size_t kMaxReportedMismatches = 20;

inline std::map<std::string, std::vector<float>> load_golden_dumps(
    const char *path) {
  std::map<std::string, std::vector<float>> dumps;
  std::ifstream in(path);
  if (!in) {
    fprintf(stderr, "hls_eval_check: could not open golden data file %s\n",
            path);
    return dumps;
  }
  const std::string begin_prefix = "begin dump: ";
  const std::string end_prefix = "end   dump: ";
  std::string line, current;
  while (std::getline(in, line)) {
    if (line.compare(0, begin_prefix.size(), begin_prefix) == 0) {
      std::string remainder = line.substr(begin_prefix.size());
      while (!remainder.empty() && remainder.back() == '\r')
        remainder.pop_back();
      std::string name = remainder;
      // A handful of testbenches print a value before checking whether to
      // start a new line, so the first value can end up glued directly onto
      // the "begin dump: NAME" line (e.g. "begin dump: x0.000000 "). A '.'
      // never appears in a real array name, so its presence means a numeric
      // value is glued on; back up over the digit run before it (the
      // integer part of that value) to recover the true name and the start
      // of the glued data.
      size_t dot = name.find('.');
      size_t data_start = std::string::npos;
      if (dot != std::string::npos) {
        size_t cut = dot;
        while (cut > 0 && isdigit(static_cast<unsigned char>(name[cut - 1])))
          --cut;
        data_start = cut;
        name.erase(cut);
      }
      current = name;
      dumps[current];
      if (data_start != std::string::npos) {
        std::istringstream iss(remainder.substr(data_start));
        float value;
        while (iss >> value) dumps[current].push_back(value);
      }
      continue;
    }
    if (line.compare(0, end_prefix.size(), end_prefix) == 0) {
      current.clear();
      continue;
    }
    if (!current.empty()) {
      std::istringstream iss(line);
      float value;
      while (iss >> value) dumps[current].push_back(value);
    }
  }
  return dumps;
}

// Accumulates a numpy.allclose-style comparison for one dumped array as
// values are streamed in the same order they were written by the dump
// (row-major, matching the golden file); `golden` is null when the array
// name is missing from the golden file.
class ArrayChecker {
 public:
  ArrayChecker(const std::vector<float> *golden, const char *name)
      : golden_(golden), name_(name) {
    if (golden_ == nullptr)
      fprintf(stderr, "hls_eval_check: no golden dump found for array %s\n",
              name_);
  }

  void add(float actual) {
    if (golden_ == nullptr || index_ >= golden_->size()) {
      ++index_;
      return;
    }
    const float expected = (*golden_)[index_++];
    const double abs_error = std::fabs(
        static_cast<double>(actual) - static_cast<double>(expected));
    const double abs_expected = std::fabs(static_cast<double>(expected));
    const double tolerance = kAtol + kRtol * abs_expected;
    abs_error_sum_ += abs_error;
    rel_error_sum_ += abs_error / (abs_expected > 1e-6 ? abs_expected : 1e-6);
    ++count_;
    if (abs_error > tolerance) {
      ++mismatch_count_;
      if (mismatch_count_ <= kMaxReportedMismatches) {
        fprintf(stderr,
                "hls_eval_check: %s[%zu] mismatch: actual=%.9f "
                "expected=%.9f abs_error=%.9g tolerance=%.9g\n",
                name_, index_ - 1, static_cast<double>(actual),
                static_cast<double>(expected), abs_error, tolerance);
      }
    }
  }

  bool passed() const {
    const bool size_ok = golden_ != nullptr && golden_->size() == index_;
    if (!size_ok) {
      fprintf(stderr,
              "hls_eval_check: %s golden/actual element count mismatch "
              "(golden=%zu, actual=%zu)\n",
              name_, golden_ ? golden_->size() : (size_t)0, index_);
    }
    const double mae = count_ ? abs_error_sum_ / count_ : 0.0;
    const double mre = count_ ? rel_error_sum_ / count_ : 0.0;
    fprintf(stderr,
            "hls_eval_check: %s MAE=%.9f MRE=%.9f mismatches=%zu/%zu "
            "(atol=%.3g rtol=%.3g)\n",
            name_, mae, mre, mismatch_count_, count_, kAtol, kRtol);
    return size_ok && mismatch_count_ == 0;
  }

 private:
  const std::vector<float> *golden_;
  const char *name_;
  size_t index_ = 0;
  double abs_error_sum_ = 0.0;
  double rel_error_sum_ = 0.0;
  size_t count_ = 0;
  size_t mismatch_count_ = 0;
};

}  // namespace hls_eval_check
