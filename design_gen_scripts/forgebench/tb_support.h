// Copied into each design so HLSFactory can run designs in isolation.
#ifndef FORGEBENCH_TB_SUPPORT_H
#define FORGEBENCH_TB_SUPPORT_H
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#ifndef FORGEBENCH_ATOL
// Maximum absolute error against the floating-point golden reference.
#define FORGEBENCH_ATOL 1e-3
#endif
#ifndef FORGEBENCH_RTOL
#define FORGEBENCH_RTOL 0.0
#endif

namespace forge_tb {
inline std::vector<double> read(const char *filename, std::size_t count) {
    std::ifstream stream(filename);
    if (!stream) throw std::runtime_error(std::string("Cannot open ") + filename);
    std::vector<double> values;
    values.reserve(count);
    std::string token;
    while (stream >> token) {
        char *end = NULL;
        double value = std::strtod(token.c_str(), &end);
        if (end == token.c_str() || *end || !std::isfinite(value))
            throw std::runtime_error(std::string("Invalid numeric data in ") + filename);
        if (values.size() == count)
            throw std::runtime_error(std::string("Too many values in ") + filename);
        values.push_back(value);
    }
    if (stream.bad() || values.size() != count)
        throw std::runtime_error(std::string("Missing values or read error in ") + filename);
    return values;
}

template<class T> void assign(T &value, const std::vector<double> &values, std::size_t &i) {
    value = values.at(i++);
}
template<class T, std::size_t N>
void assign(T (&array)[N], const std::vector<double> &values, std::size_t &i) {
    for (std::size_t j = 0; j < N; ++j) assign(array[j], values, i);
}
template<class T> void load(T &array, const char *filename, std::size_t count) {
    std::vector<double> values = read(filename, count);
    std::size_t i = 0;
    assign(array, values, i);
    if (i != count) throw std::runtime_error("Array size disagrees with fixture size");
}
template<class T> void poison(T &value) { value = -7.0; }
template<class T, std::size_t N> void poison(T (&array)[N]) {
    for (std::size_t i = 0; i < N; ++i) poison(array[i]);
}

// Select a representable poison far from each expected value, including -7.
template<class T>
void poison_expected(T &value, const std::vector<double> &expected, std::size_t &i) {
    value = expected.at(i++) >= 0 ? -16.0 : 15.0;
}
template<class T, std::size_t N>
void poison_expected(T (&array)[N], const std::vector<double> &expected, std::size_t &i) {
    for (std::size_t j = 0; j < N; ++j) poison_expected(array[j], expected, i);
}
template<class T> void poison(T &array, const std::vector<double> &expected) {
    std::size_t i = 0;
    poison_expected(array, expected, i);
    if (i != expected.size()) throw std::runtime_error("Poison size disagrees with output size");
}

struct Comparison {
    const char *name;
    const std::vector<double> &expected;
    std::size_t index;
    std::size_t mismatches;
    double max_error;
    FILE *dump;
    void value(double actual) {
        const double golden = expected.at(index);
        const double error = std::fabs(actual - golden);
        if (error > max_error) max_error = error;
        if (!std::isfinite(actual) || error > FORGEBENCH_ATOL + FORGEBENCH_RTOL * std::fabs(golden)) {
            if (mismatches < 8)
                std::fprintf(stderr, "%s[%zu]: actual=%.12g expected=%.12g abs_error=%.12g\n",
                             name, index, actual, golden, error);
            ++mismatches;
        }
        if (std::fprintf(dump, "%.12g\n", actual) < 0)
            throw std::runtime_error("Cannot write actual output");
        ++index;
    }
};
template<class T> void compare_values(const T &value, Comparison &c) { c.value(double(value)); }
template<class T, std::size_t N> void compare_values(const T (&array)[N], Comparison &c) {
    for (std::size_t i = 0; i < N; ++i) compare_values(array[i], c);
}
template<class T>
bool check(const T &array, const std::vector<double> &golden, const char *name, const char *dump_name) {
    FILE *dump = std::fopen(dump_name, "w");
    if (!dump) throw std::runtime_error(std::string("Cannot create ") + dump_name);
    Comparison c = {name, golden, 0, 0, 0.0, dump};
    try { compare_values(array, c); }
    catch (...) { std::fclose(dump); throw; }
    if (std::fclose(dump)) throw std::runtime_error("Cannot close actual output");
    if (c.index != golden.size()) throw std::runtime_error("Golden size disagrees with output size");
    std::printf("%s: %s (%zu/%zu mismatches, max_abs_error=%.12g, atol=%.12g, rtol=%.12g)\n",
                c.mismatches ? "FAIL" : "PASS", name, c.mismatches, c.index,
                c.max_error, double(FORGEBENCH_ATOL), double(FORGEBENCH_RTOL));
    return c.mismatches == 0;
}
} // namespace forge_tb
#endif
