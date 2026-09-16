// ap_fixed testbench: loads input.data/check.data as float (same reference
// data as the float version), runs the ap_fixed workload(), and compares
// with fpx_check's numpy.allclose-style tolerance.
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>

#include "fpx_check.h"
#include "dilate.h"
#include "support.h"

extern "C" void workload(fixed_t result[GRID_ROWS * GRID_COLS],
                          fixed_t img[(GRID_ROWS + 2 * MAX_RADIUS) * GRID_COLS]);

int main() {
  static fixed_t img[(GRID_ROWS + 2 * MAX_RADIUS) * GRID_COLS] = {};
  static fixed_t result[GRID_ROWS * GRID_COLS];
  static float result_ref[GRID_ROWS * GRID_COLS];
  static float tmp_img[GRID_ROWS * GRID_COLS];

  int fd = open("input.data", O_RDONLY);
  if (fd < 0) { perror("input.data"); return 1; }
  char *p = readfile(fd);
  parse_float_array(find_section_start(p, 1), tmp_img, GRID_ROWS * GRID_COLS);
  free(p);
  int starting_idx = MAX_RADIUS * GRID_COLS;
  for (int i = 0; i < GRID_ROWS; ++i)
    for (int j = 0; j < GRID_COLS; ++j)
      img[starting_idx + i * GRID_COLS + j] = tmp_img[i * GRID_COLS + j];

  workload(result, img);

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
