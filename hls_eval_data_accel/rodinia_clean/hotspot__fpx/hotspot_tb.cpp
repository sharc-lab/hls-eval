// ap_fixed testbench: loads input.data (temp, power) as float (same
// reference data as the float version), runs the ap_fixed workload(), and
// compares with fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "hotspot.h"
#include "support.h"

extern "C" void workload(fixed_t result[GRID_ROWS * GRID_COLS],
                          fixed_t temp[GRID_ROWS * GRID_COLS],
                          fixed_t power[GRID_ROWS * GRID_COLS]);

static float temp_f[GRID_ROWS * GRID_COLS];
static float power_f[GRID_ROWS * GRID_COLS];
static float temp_ref[GRID_ROWS * GRID_COLS];

static fixed_t result[GRID_ROWS * GRID_COLS] = {};
static fixed_t temp[GRID_ROWS * GRID_COLS];
static fixed_t power[GRID_ROWS * GRID_COLS];

int main() {
  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), temp_f, GRID_ROWS * GRID_COLS);
  parse_float_array(find_section_start(p, 2), power_f, GRID_ROWS * GRID_COLS);
  free(p);

  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++) temp[i] = temp_f[i];
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++) power[i] = power_f[i];

  workload(result, temp, power);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), temp_ref, GRID_ROWS * GRID_COLS);
  free(p2);

  // Note: SIM_TIME is even, so the last-updated buffer is `temp` (workload
  // alternates result<->temp), matching the original testbench.
  fpx_check::ArrayChecker checker("temp");
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++)
    checker.add((double)(float)temp[i], (double)temp_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
