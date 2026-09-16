// ap_fixed testbench: loads input.data/check.data as float (same reference
// data as the float version), runs the ap_fixed workload(), and compares
// with fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "lud.h"
#include "support.h"

extern "C" void workload(fixed_t result[GRID_ROWS * GRID_COLS]);

static void load(const char *filename, fixed_t out[GRID_ROWS * GRID_COLS]) {
  static float tmp[GRID_ROWS * GRID_COLS];
  int fd = open(filename, O_RDONLY);
  if (fd < 0) { perror(filename); exit(1); }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), tmp, GRID_ROWS * GRID_COLS);
  free(p);
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++) out[i] = tmp[i];
}

static void load_float(const char *filename, float out[GRID_ROWS * GRID_COLS]) {
  int fd = open(filename, O_RDONLY);
  if (fd < 0) { perror(filename); exit(1); }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), out, GRID_ROWS * GRID_COLS);
  free(p);
}

int main() {
  static fixed_t result[GRID_ROWS * GRID_COLS];
  static float reference[GRID_ROWS * GRID_COLS];

  load("input.data", result);
  workload(result);
  load_float("check.data", reference);

  fpx_check::ArrayChecker checker("result");
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++)
    checker.add((double)(float)result[i], (double)reference[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
