// ap_fixed testbench: loads input.data (grad_x, grad_y) and check.data as
// float (same reference data as the float version), runs the ap_fixed
// workload(), and compares with fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "lc_gicov.h"
#include "support.h"

extern "C" void workload(fixed_t result[GRID_ROWS * GRID_COLS],
                          fixed_t grad_x[GRID_ROWS * GRID_COLS],
                          fixed_t grad_y[GRID_ROWS * GRID_COLS]);

int main() {
  static fixed_t result[GRID_ROWS * GRID_COLS] = {};
  static fixed_t grad_x[GRID_ROWS * GRID_COLS];
  static fixed_t grad_y[GRID_ROWS * GRID_COLS];
  static float tmp_x[GRID_ROWS * GRID_COLS];
  static float tmp_y[GRID_ROWS * GRID_COLS];
  static float result_ref[GRID_ROWS * GRID_COLS];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), tmp_x, GRID_ROWS * GRID_COLS);
  parse_float_array(find_section_start(p, 2), tmp_y, GRID_ROWS * GRID_COLS);
  free(p);
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++) {
    grad_x[i] = tmp_x[i];
    grad_y[i] = tmp_y[i];
  }

  workload(result, grad_x, grad_y);

  int fd2 = open("check.data", O_RDONLY);
  if (fd2 < 0) { perror("check.data"); return 1; }
  char *p2 = readfile(fd2);
  parse_float_array(find_section_start(p2, 1), result_ref, GRID_ROWS * GRID_COLS);
  free(p2);

  fpx_check::ArrayChecker checker("result");
  for (int i = 0; i < GRID_ROWS * GRID_COLS; i++)
    checker.add((double)(float)result[i], (double)result_ref[i]);

  bool pass = checker.passed();
  printf(pass ? "PASS\n" : "FAIL\n");
  return pass ? 0 : 1;
}
